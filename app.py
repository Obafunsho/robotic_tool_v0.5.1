"""
Robotic Programme Decision Tool: web interface (v1.1).

Run locally:   streamlit run app.py

One page, essentials first: hospital type (example rota), number of robots, platform,
the two-week rota, headline results and the Word business case. Everything else sits in
one "Advanced settings" section at the bottom. The page is laid out with containers so
that settings chosen in Advanced settings feed the results shown above it. Nothing
entered is stored on the server.
"""
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import benchmark as BM
import business_case as BC
import defaults as D
import engine as E
import register_xlsx as RX
import sensitivity as S
import templates as T

HERE = Path(__file__).parent
st.set_page_config(page_title="Robotic Programme Decision Tool", layout="wide",
                   page_icon=str(HERE / "static" / "favicon.png"), initial_sidebar_state="collapsed")

# Plain, high-contrast layout in the style of public digital services: Arial, black text,
# simple tables. It is not an NHS product and uses no NHS name or logo.
st.markdown("""
<style>
  [data-testid="stDecoration"], [data-testid="stMainMenu"], #MainMenu, footer,
  [data-testid="stAppDeployButton"], .stDeployButton, [data-testid="stSidebarCollapsedControl"],
  [data-testid="stExpandSidebarButton"] { display: none !important; }
  header[data-testid="stHeader"] { background: transparent; }
  .block-container, [data-testid="stMainBlockContainer"] { padding: 1.4rem 2rem 2rem 2rem; max-width: 1640px; }
  h1 { font-weight: 700; font-size: 2.1rem; border-bottom: 1px solid #0B0C0C; padding-bottom: 0.4rem; }
  h2, h3 { font-weight: 700; color: #0B0C0C; }
  [data-testid="stMetricValue"] { font-weight: 700; color: #0B0C0C; }
  [data-testid="stMetricLabel"] p { font-size: 0.9rem; color: #0B0C0C; }
  a { color: #0B0C0C; text-decoration: underline; }
  /* buttons: white text on black (primary) and black text on white (secondary), always readable */
  [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] p,
  button[kind="primary"], button[kind="primary"] p,
  [data-testid="stDownloadButton"] button[kind="primary"], [data-testid="stDownloadButton"] button[kind="primary"] p {
      background-color: #0B0C0C !important; color: #FFFFFF !important; border-color: #0B0C0C !important; }
  [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondary"] p,
  button[kind="secondary"], button[kind="secondary"] p {
      background-color: #FFFFFF !important; color: #0B0C0C !important; border-color: #0B0C0C !important; }
  /* dropdown menus: black text on white, selected or hovered option on light grey */
  [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"], [role="listbox"],
  [role="option"] { background-color: #FFFFFF !important; color: #0B0C0C !important; }
  [role="option"] * { color: #0B0C0C !important; }
  [role="option"]:hover, [role="option"][aria-selected="true"] { background-color: #E8E8E8 !important; }
  [data-baseweb="select"] div { color: #0B0C0C !important; }
  .rpdt-intro { font-size: 1.1rem; color: #0B0C0C; margin: 0.2rem 0 0.4rem 0; }
  .rpdt-note { border-left: 5px solid #0B0C0C; background: #F3F2F1; padding: 0.7rem 1rem;
               margin: 0.4rem 0 1rem 0; font-size: 1rem; color: #0B0C0C; }
  .rpdt-meta { color: #0B0C0C; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

STATUS_STYLE = {"Green": "background-color:#CCE2D8", "Amber": "background-color:#FFF2CC",
                "Red": "background-color:#F6D7D2"}
PROSTATE_OPTIONS = ["Open surgery", "Robotic surgery at another centre"]
HOSPITALS = {"medium": "Medium DGH (under 800 beds)", "large": "Large hospital (800 beds or more)"}
TARIFF_COL = f"{D.TARIFF_FIELD_LABEL} (£ per operation)"
COVER_FIELDS = ["prepared_by", "sro", "clinical_lead", "finance_lead", "version", "status", "date"]


def gbp(x):
    if x is None:
        return "n/a"
    return f"-£{abs(x):,.0f}" if x < 0 else f"£{x:,.0f}"


def gbpm(x):
    return f"£{x / 1e6:,.2f}M"


def note(text):
    st.markdown(f'<div class="rpdt-note">{text}</div>', unsafe_allow_html=True)


ss = st.session_state
ss.setdefault("grid_version", 0)
defaults = dict(w_hospital=HOSPITALS["medium"], w_robots=1, w_platform="platform_b", w_existing="0",
                w_price_mode="list", w_central=0, w_evidence="central", w_capvalue=False,
                w_prost=PROSTATE_OPTIONS[0], w_basis="per_robot", w_realisation=100)
for k, v in defaults.items():
    ss.setdefault(k, v)

# ---------------------------------------------------------------------------
# Page layout (visual order); filled below in calculation order
# ---------------------------------------------------------------------------
st.title("Robotic Programme Decision Tool")
st.markdown(f'<p class="rpdt-intro">{D.INTRO_LINE}</p>', unsafe_allow_html=True)
st.markdown('<p class="rpdt-meta">Draft: do not use the figures for approval until the assumptions register has '
            'been signed off.</p>', unsafe_allow_html=True)
top = st.container()
rota_ct = st.container()
results_ct = st.container()
bc_ct = st.container()
adv = st.expander("Advanced settings")

# ---------------------------------------------------------------------------
# Main choices
# ---------------------------------------------------------------------------
with top:
    c1, c2, c3 = st.columns([2, 1, 3])
    hospital_label = c1.selectbox("Hospital type (sets the example rota)", list(HOSPITALS.values()), key="w_hospital")
    robots = c2.radio("Number of robots", [1, 2], horizontal=True, key="w_robots")
    platform = c3.selectbox("Platform", list(D.PLATFORMS), key="w_platform",
                            format_func=lambda k: D.PLATFORMS[k]["label"])
hospital = next(k for k, v in HOSPITALS.items() if v == hospital_label)
preset = ("medium_dgh_" if hospital == "medium" else "large_") + str(robots)
pf_default = D.PLATFORMS[platform]

# ---------------------------------------------------------------------------
# Advanced settings: inputs (drawn in the expander at the bottom of the page)
# ---------------------------------------------------------------------------
with adv:
    t_set, t_cost, t_clin, t_reg, t_res, t_sens, t_cover = st.tabs(
        ["Settings", "Prices, unit costs and tariff", "Procedures and clinical assumptions", "Assumptions register",
         "Detailed results", "Sensitivity and benchmark", "Business case cover"])
    with t_set:
        a1, a2 = st.columns(2)
        existing = a1.selectbox("Existing soft-tissue robots at the trust (stated in the business case)",
                                D.EXISTING_ROBOT_OPTIONS, key="w_existing")
        realisation = a2.number_input("Rota operations that go ahead (%)", min_value=50, max_value=100, step=1,
                                      key="w_realisation",
                                      help="Allows for cancellations and under-runs. 100% means every rota operation "
                                           "goes ahead (placeholder).")
        evidence = a1.selectbox("Clinical benefit setting", list(D.EVIDENCE_SETTINGS), key="w_evidence",
                                format_func=lambda k: D.EVIDENCE_LABELS[k])
        prost = a2.radio("Prostatectomy comparator", PROSTATE_OPTIONS, key="w_prost")
        price_mode = a1.selectbox("Instrument price", ["list", "standard_discount", "volume_discount", "custom"],
                                  key="w_price_mode", format_func=lambda k: D.INSTRUMENT_PRICE_LABELS[k])
        instrument_price = price_mode
        if price_mode == "custom":
            ss.setdefault("w_quote", float(pf_default.get("instruments_per_case", 0)))
            instrument_price = a1.number_input("Trust quote: instruments per operation (£)", min_value=0.0,
                                               step=50.0, key="w_quote")
        central = 0
        if pf_default["model"] == "purchase":
            central = a2.selectbox("Central capital per robot", D.CENTRAL_CAPITAL_OPTIONS, key="w_central",
                                   format_func=lambda v: "None (trust pays)" if v == 0 else f"£{v:,.0f}")
        basis = None
        if pf_default["model"] in ("managed_service", "per_procedure"):
            basis = a2.radio("Contract volumes apply", ["per_robot", "per_contract"], key="w_basis",
                             format_func=lambda k: D.CONTRACT_BASIS_LABELS[k].capitalize())
        capacity_value = a1.checkbox("Value released bed-days as extra elective activity", key="w_capvalue")

base_cfg = E.build_config(preset, platform, evidence, template=None)
proc_keys = T.procedure_keys(base_cfg)

with adv:
    with t_cost:
        st.markdown("**Platform prices**")
        pf_over = {}
        fields = {"purchase": [("capital", "Capital per robot (£)"), ("trade_in", "Trade-in credit (£)"),
                               ("asset_life_years", "Asset life (years)"),
                               ("maintenance_per_year", "Maintenance per robot per year (£)")],
                  "managed_service": [("annual_fee", "Annual fee per robot (£)"),
                                      ("cases_included", "Operations included per year"),
                                      ("excess_fee_per_case", "Excess fee per operation (£)")],
                  "lease": [("lease_per_year", "Lease per robot per year (£)"),
                            ("maintenance_per_year", "Maintenance per year (£)")],
                  "per_procedure": [("fee_per_case", "Fee per operation (£)"),
                                    ("minimum_cases_per_year", "Minimum operations per year")]}
        cols = st.columns(4)
        for i, (f, lbl) in enumerate(fields[pf_default["model"]]):
            key = f"pf-{platform}-{f}"
            ss.setdefault(key, float(pf_default[f]))
            v = cols[i % 4].number_input(lbl, min_value=0.0, key=key)
            if v != pf_default[f]:
                pf_over[f] = v
        if price_mode != "custom" and not pf_default.get("instruments_included"):
            key = f"inst-{platform}"
            ss.setdefault(key, float(pf_default.get("instruments_per_case", 0)))
            v = st.number_input("Instrument list price per operation (£)", min_value=0.0, key=key)
            if v != pf_default.get("instruments_per_case", 0):
                pf_over["instruments_per_case"] = v
        if basis is not None and basis != pf_default.get("contract_volume_basis", "per_robot"):
            pf_over["contract_volume_basis"] = basis
        st.caption(f"Price basis: {pf_default['source']}")
        st.markdown("**Unit costs and staffing**")
        uc_rows = [{"key": k, "Cost": D.UNIT_COST_LABELS[k], "Value": float(base_cfg["unit_costs"][k])}
                   for k in ("bed_day", "theatre_minute", "decontamination_per_case", "reoperation",
                             "major_complication", "readmission", "conversion")]
        uc_rows += [{"key": "sfa_cost_per_wte", "Cost": "Surgical first assistant: cost per WTE (£)",
                     "Value": float(base_cfg["programme"]["sfa_cost_per_wte"])},
                    {"key": "sfa_wte_per_robot", "Cost": "Surgical first assistant: WTE per robot",
                     "Value": float(base_cfg["programme"]["sfa_wte_per_robot"])}]
        uc_ed = st.data_editor(pd.DataFrame(uc_rows), key="uc", hide_index=True, width="stretch",
                               disabled=["key", "Cost"],
                               column_config={"key": None, "Value": st.column_config.NumberColumn(min_value=0.0)})
        st.caption(D.EVIDENCE_NOTES["bed_day"])
        st.markdown(f"**{D.TARIFF_FIELD_LABEL}** (cash case only)")
        st.caption("Only the difference over what the trust would earn for the same patient without the robot. It "
                   "reduces the trust's cash cost but is excluded from the economic view and from cost per outcome.")
        tar = pd.DataFrame([dict(group=k, Procedure=base_cfg["groups"][k]["label"],
                                 **{TARIFF_COL: base_cfg["groups"][k].get("tariff_uplift", 0.0),
                                    "Source": D.TARIFF_SOURCES.get(k, D.DEFAULT_TARIFF_SOURCE)}) for k in proc_keys])
        tar_ed = st.data_editor(tar, key="tariff", hide_index=True, width="stretch",
                                disabled=["group", "Procedure", "Source"],
                                column_config={"group": None, TARIFF_COL: st.column_config.NumberColumn(step=50)})

    with t_clin:
        st.markdown("**Procedures**")
        st.dataframe(pd.DataFrame([{"Specialty": base_cfg["groups"][k]["specialty"],
                                    "Procedure": base_cfg["groups"][k]["label"],
                                    "Complexity": base_cfg["groups"][k]["complexity"],
                                    "30-day benefit": D.BENEFIT_STATUS_LABELS[base_cfg["groups"][k]["benefit_status"]]}
                                   for k in proc_keys]), width="stretch", hide_index=True)
        st.caption(f"{D.NOT_MODELLED_NOTE} Complexity is descriptive only; operations come from the rota.")
        st.markdown("**Clinical assumptions at 30 days**")
        st.caption("Reductions per operation, robotic versus each comparator. 'Share' is the proportion of these "
                   "patients who would have had that comparator without the robot. Changes are flagged everywhere.")
        pr_df = pd.DataFrame(E.prior_rows(base_cfg))
        pr_df["Without the robot"] = pr_df["comparator"].map(D.COMPARATOR_LABELS)
        pr_df = pr_df[["group", "comparator", "specialty", "Without the robot", "share", "los", "conv", "reop",
                       "comp", "readm", "extra_minutes"]]
        pr_ed = st.data_editor(pr_df, key="prior", width="stretch", hide_index=True,
                               disabled=["group", "comparator", "specialty", "Without the robot"],
                               column_config={"share": "Share", "los": "Bed-days saved", "conv": "Conversions avoided",
                                              "reop": "Returns to theatre avoided", "comp": "Complications avoided",
                                              "readm": "Readmissions avoided", "extra_minutes": "Extra minutes",
                                              "specialty": "Procedure", "group": None, "comparator": None})

    with t_reg:
        st.write("The full register: one row per procedure and assumption, with value, source, evidence grade and "
                 "status, and columns for a reviewer's decision (agree, change to, needs evidence) and comment. ID "
                 "and Value are locked. Load a completed file to apply the changes.")
        st.download_button("Download the assumptions register (.xlsx)", RX.export(),
                           file_name=f"assumptions_register_v{D.ENGINE_VERSION}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        reg_up = st.file_uploader("Load a reviewed register (.xlsx)", type=["xlsx"], key="reg_upload")
        if reg_up is not None and ss.get("last_reg_upload") != reg_up.file_id:
            ss["last_reg_upload"] = reg_up.file_id
            ss["register_review"] = RX.load(reg_up.getvalue())
        review = ss.get("register_review")
        if review:
            st.write(f"Review loaded: {len(review['changes'])} changes applied, "
                     f"{len(review['needs_evidence'])} items marked 'needs evidence'.")
            for e_ in review.get("errors", []):
                st.error(e_)
            if st.button("Remove the loaded review"):
                ss["register_review"] = None
                st.rerun()

    with t_cover:
        cover_defaults = dict(prepared_by="[Name, role]", sro="[Name, role]", clinical_lead="[Name, role]",
                              finance_lead="[Name, role]", version="Draft 0.1", status=BC.DRAFT_STATUS,
                              date=date.today().strftime("%d %B %Y"))
        labels = dict(prepared_by="Prepared by", sro="Senior responsible owner", clinical_lead="Clinical lead",
                      finance_lead="Finance lead", version="Version", status="Status", date="Date")
        cc = st.columns(2)
        cover = {}
        for i, f in enumerate(COVER_FIELDS):
            ss.setdefault(f"c_{f}", cover_defaults[f])
            cover[f] = cc[i % 2].text_input(labels[f], key=f"c_{f}")

# ---------------------------------------------------------------------------
# The rota
# ---------------------------------------------------------------------------
grid_key = (hospital, robots)
if ss.get("grid") is None or ss.get("grid_key") != grid_key:
    ss["grid"] = T.example_rota(hospital, robots)
    ss["grid_version"] += 1
ss["grid_key"] = grid_key

with rota_ct:
    st.subheader("Two-week robot rota")
    st.write("For each day, set the sessions available (0, 2 or 3). For each session, choose a procedure and the "
             "number of operations; for an operation running over 2 or 3 sessions, choose the same procedure in the "
             "next session and set operations to 'cont.'.")
    st.caption(f"{D.NOT_MODELLED_NOTE} Session 3 is unavailable on 2-session days; use 0 for days without robot "
               "sessions. Utilisation is sessions booked divided by sessions available.")
    popts, copts = T.procedure_options(base_cfg), T.case_options()
    edited = []
    for rb in range(robots):
        rows = ss["grid"][rb] if rb < len(ss["grid"]) else T.empty_robot()
        if robots > 1:
            st.markdown(f"**Robot {rb + 1}**")
        colcfg = {"Week": st.column_config.NumberColumn(disabled=True, width=50),
                  "Day": st.column_config.TextColumn(disabled=True, width=50),
                  "Sessions available": st.column_config.SelectboxColumn(
                      "Sessions", options=D.SESSIONS_AVAILABLE_OPTIONS, required=True, width=75)}
        for i, s_ in enumerate(D.SESSIONS, start=1):
            colcfg[f"{D.SESSION_LABELS[s_]}: procedure"] = st.column_config.SelectboxColumn(
                D.SESSION_LABELS[s_], options=popts, required=True, width=205)
            colcfg[f"Session {i} operations"] = st.column_config.SelectboxColumn(
                "Operations", options=copts, required=True, width=95)
        df = st.data_editor(pd.DataFrame(T.to_ui_rows(base_cfg, rows), columns=T.ui_columns()),
                            key=f"grid-{rb}-{ss['grid_version']}", hide_index=True, width="stretch",
                            height=36 * 15, column_config=colcfg, num_rows="fixed")
        edited.append(T.from_ui_rows(base_cfg, df.to_dict("records")))
    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button("Reset to the example rota"):
        ss["grid"] = T.example_rota(hospital, robots)
        ss["grid_version"] += 1
        st.rerun()
    if b2.button("Clear the rota"):
        ss["grid"] = T.empty_grid(robots)
        ss["grid_version"] += 1
        st.rerun()

# ---------------------------------------------------------------------------
# Assemble the configuration and run
# ---------------------------------------------------------------------------
group_over = {}
for r_ in tar_ed.to_dict("records"):
    if float(r_[TARIFF_COL] or 0) != base_cfg["groups"][r_["group"]].get("tariff_uplift", 0.0):
        group_over.setdefault(r_["group"], {})["tariff_uplift"] = float(r_[TARIFF_COL] or 0)
for k, o in E.overrides_from_prior_rows(pr_ed.to_dict("records")).items():
    changed = {f: v for f, v in o.items() if v != D.PROCEDURE_GROUPS[k].get(f)}
    if changed:
        group_over.setdefault(k, {}).update(changed)
if prost == PROSTATE_OPTIONS[1]:
    group_over.setdefault("prostatectomy", {}).update(BC.PROSTATE_ELSEWHERE["prostatectomy"])
uc_over, prog_over = {}, {}
for r_ in uc_ed.to_dict("records"):
    v = float(r_["Value"] or 0)
    if r_["key"] in D.UNIT_COSTS and v != D.UNIT_COSTS[r_["key"]]:
        uc_over[r_["key"]] = v
    elif r_["key"] in ("sfa_cost_per_wte", "sfa_wte_per_robot") and v != D.PROGRAMME[r_["key"]]:
        prog_over[r_["key"]] = v
configuration = dict(preset=preset, robots=robots, platform=platform, evidence=evidence,
                     instrument_price=instrument_price, central_capital_per_robot=central,
                     existing_robots=existing, groups=group_over, unit_costs=uc_over, platform_overrides=pf_over,
                     template=edited, register_review=ss.get("register_review"),
                     programme=dict(include_capacity_value=capacity_value,
                                    realisation_factor=float(realisation) / 100, **prog_over))
try:
    res = E.run(E.build_config(**BC.configure(dict(configuration=configuration))))
    error = None
except ValueError as exc:
    res, error = None, str(exc)

# ---------------------------------------------------------------------------
# Headline results (main page)
# ---------------------------------------------------------------------------
with results_ct:
    if error:
        st.error(f"Input problem: {error}")
    else:
        cfg = res["config"]
        y3, t = res["yearly"][2], res["totals"]
        rota_errors = [w[len("Rota: "):] for w in res["warnings"] if w.startswith("Rota: ")]
        for w in rota_errors:
            st.warning(w)
        st.subheader("What the programme buys for patients each year (year 3)")
        c = st.columns(4)
        c[0].metric("Robotic operations", f"{y3['cases']:,.0f}")
        c[1].metric("Open operations avoided", f"{y3['open_avoided']:,.0f}")
        c[2].metric("Bed-days released", f"{y3['bed_days']:,.0f}")
        c[3].metric("Serious events avoided", f"{y3['reoperations'] + y3['complications'] + y3['readmissions']:,.1f}")
        nm_note = BC.not_modelled_note(res)
        if nm_note:
            note(nm_note)
        st.subheader("Cost per outcome (five years)")
        c = st.columns(4)
        c[0].metric("Extra cost per operation", gbp(t["cost_per_case"]))
        c[1].metric("Extra cost per open operation avoided", gbp(t["cost_per_open_operation_avoided"]))
        c[2].metric("Extra cost per bed-day released", gbp(t["cost_per_bed_day_released"]))
        c[3].metric("Extra cost per serious event avoided", gbp(t["cost_per_serious_event_avoided"]))
        st.caption("Each ratio divides the whole five-year extra cost by one consequence; they must not be added. "
                   "Neither 30-day cost avoided nor the tariff uplift is deducted.")
        st.subheader("Five-year cost to the trust")
        c = st.columns(4)
        c[0].metric("Five-year extra cost (revenue)", gbpm(t["extra_cost"]))
        c[1].metric("Less tariff uplift (difference over existing tariff)", gbpm(t["tariff_income"]))
        c[2].metric("Net cash cost to the trust", gbpm(t["net_cash_cost"]))
        c[3].metric("Utilisation (sessions booked / available)", f"{res['booked_utilisation']:.0%}")
        note(BC.break_even_sentence(res["break_even"]))
        st.subheader("Spending guardrails")
        g = pd.DataFrame([dict(Check=x["check"], Result=x["value"], Status=x["status"].capitalize(), Rule=x["rule"])
                          for x in res["guardrails"]])
        st.dataframe(g.style.map(lambda v: STATUS_STYLE.get(v, ""), subset=["Status"]), width="stretch",
                     hide_index=True)

# ---------------------------------------------------------------------------
# Business case (main page)
# ---------------------------------------------------------------------------
with bc_ct:
    st.subheader("Business case")
    ss.setdefault("c_trust_name", "[Trust name]")
    trust = st.text_input("Trust name", key="c_trust_name")
    st.caption("A Five Case Model Word document built from these inputs. Cover details are in Advanced settings.")
    case = dict(cover=dict(trust_name=trust, **cover), configuration=configuration)
    if error:
        st.error("Fix the input problem before generating the business case.")
    elif st.button("Generate Word business case", type="primary"):
        with st.spinner("Building the business case"):
            data, _ = BC.build_docx_bytes(case)
        name = "".join(ch for ch in trust if ch.isalnum() or ch in " -_").strip() or "Trust"
        st.download_button("Download business case (.docx)", data, file_name=f"Robotic_business_case_{name}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           type="primary")

# ---------------------------------------------------------------------------
# Advanced settings: detailed results, sensitivity and benchmark
# ---------------------------------------------------------------------------
with adv:
    with t_res:
        if error:
            st.error("Fix the input problem first.")
        else:
            fy = pd.DataFrame([{"Year": y["year"], "Operations": f"{y['cases']:,.0f}",
                                "Bed-days released": f"{y['bed_days']:,.0f}", "Extra cost": gbp(y["extra_cost"]),
                                "Tariff uplift": gbp(y["tariff_income"]), "Net cash cost": gbp(y["net_cash_cost"]),
                                "30-day cost avoided (not cash)": gbp(y["offsets"])} for y in res["yearly"]])
            st.dataframe(fy, width="stretch", hide_index=True)
            st.caption(BC.TARIFF_NOTE + f" Net present cost to the NHS (economic view): "
                       f"{gbpm(res['economic']['net_present_cost'])}. Capital funded by the trust: "
                       f"{gbp(res['capital']['trust_funded'])}.")
            parts = []
            for y in res["yearly"]:
                for key, lab in [("platform_fixed", "Platform"), ("instruments", "Instruments"),
                                 ("decontamination", "Sterile services"), ("staffing", "Surgical first assistant"),
                                 ("theatre_time_cost", "Extra theatre time"),
                                 ("implementation", "Implementation and training"), ("theatre_modification", "Theatre works")]:
                    if y[key]:
                        parts.append(dict(Year=f"Year {y['year']}", Component=lab, Cost=y[key]))
            bars = alt.Chart(pd.DataFrame(parts)).mark_bar().encode(
                x=alt.X("Year:N", title=None), y=alt.Y("sum(Cost):Q", title="£"),
                color=alt.Color("Component:N", scale=alt.Scale(scheme="greys")))
            line = alt.Chart(pd.DataFrame([dict(Year=f"Year {y['year']}", Avoided=y["offsets"]) for y in res["yearly"]])
                             ).mark_line(point=True, color="#000000", strokeDash=[4, 3]).encode(x="Year:N", y="Avoided:Q")
            st.altair_chart(bars + line, width="stretch")
            st.caption("Bars: extra cost to the trust. Dashed line: 30-day cost avoided (not cash).")
            prow = [{"Procedure": go["label"], "30-day benefit": D.BENEFIT_STATUS_LABELS[go["benefit_status"]],
                     "Sessions per fortnight": go["sessions_per_fortnight"],
                     "Operations per fortnight": res["template_summary"]["cases_per_fortnight"][k],
                     "Operations a year": round(go["planned_cases"])}
                    for k, go in res["groups"].items() if go["sessions_per_fortnight"]]
            st.dataframe(pd.DataFrame(prow), width="stretch", hide_index=True)
            pt = res["price_targets"]
            if pt["applicable"]:
                st.write(f"Instrument price targets (net of 30-day cost avoided): current {gbp(pt['current_price'])} "
                         f"per operation; needed for {gbp(pt['target_net_cost_per_bed_day'])} per bed-day released: "
                         f"{gbp(pt['price_for_target']) if pt['price_for_target'] is not None else 'not achievable'}; "
                         f"needed for budget neutrality: "
                         f"{gbp(pt['budget_neutral_price']) if pt['budget_neutral_price'] is not None else 'not achievable'}.")
            other = [w for w in res["warnings"] if not w.startswith("Rota: ")]
            if other:
                st.markdown("**Warnings**")
                for w in other:
                    st.warning(w)
            if res["user_modified"]:
                st.markdown("**Assumptions changed from defaults**")
                st.dataframe(pd.DataFrame([{"Assumption": E.describe_item(cfg, m["item"]),
                                            "Default": E.fmt_value(m["default"]), "Used": E.fmt_value(m["used"])}
                                           for m in res["user_modified"]]), width="stretch", hide_index=True)
    with t_sens:
        if not error:
            metric = st.selectbox("Result", list(S.METRICS), index=1, format_func=lambda k: S.METRICS[k][0])
            tor = S.tornado(cfg, metric, res)
            if tor["bars"]:
                rows = []
                for b in tor["bars"]:
                    for lvl, lab in (("low", b["low_label"]), ("high", b["high_label"])):
                        rows.append(dict(Assumption=b["name"], Setting=f"{lvl.capitalize()}: {lab}",
                                         Level=lvl.capitalize(), start=tor["base"], end=b[lvl], swing=b["swing"]))
                order = [b["name"] for b in tor["bars"]]
                chart = alt.Chart(pd.DataFrame(rows)).mark_bar().encode(
                    y=alt.Y("Assumption:N", sort=order, title=None, axis=alt.Axis(labelLimit=0)),
                    x=alt.X("start:Q", title=tor["metric_label"] + " (£)"), x2="end:Q",
                    color=alt.Color("Level:N", scale=alt.Scale(domain=["Low", "High"], range=["#9E9E9E", "#0B0C0C"])),
                    tooltip=["Assumption", "Setting", alt.Tooltip("end:Q", format=",.0f")])
                rule = alt.Chart(pd.DataFrame([{"base": tor["base"]}])).mark_rule(color="#6B7280").encode(x="base:Q")
                st.altair_chart((chart + rule).properties(height=36 * len(order) + 40), width="stretch")
                st.caption(f"Base case {gbp(tor['base'])}. Each assumption is moved on its own; the rota is held "
                           "fixed. Ranges are placeholders for expert review.")
            st.markdown("**Comparison with a benchmark programme**")
            bench = BM.run_benchmark(cfg)
            st.dataframe(pd.DataFrame([dict(Measure=a, **{"This proposal": b, "Benchmark": c, "Benchmark source": d})
                                       for a, b, c, d in BM.comparison_rows(res, bench)]), width="stretch",
                         hide_index=True)
