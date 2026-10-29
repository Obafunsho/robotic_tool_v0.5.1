"""
Robotic Programme Decision Tool: web interface (v0.6).

Run locally:   streamlit run app.py
The main input is a two-week theatre template per robot. All calculations come
from engine.py; the Word document, which remains the main output, from
business_case.py. Nothing entered is stored on the server; a case can be saved as
an inputs file (.json) and reloaded.
"""
import copy
import json
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import benchmark as BM
import business_case as BC
import defaults as D
import engine as E
import inputs_io as IO
import register as RG
import register_xlsx as RX
import sensitivity as S
import templates as T

HERE = Path(__file__).parent
st.set_page_config(page_title="Robotic Programme Decision Tool", layout="wide",
                   page_icon=str(HERE / "static" / "favicon.png"))

# Restrained institutional styling. Streamlit's own chrome is hidden where its
# configuration and stable test identifiers allow (see README: Streamlit limits).
st.markdown("""
<style>
  [data-testid="stDecoration"], [data-testid="stMainMenu"], #MainMenu, footer,
  [data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
  header[data-testid="stHeader"] { background: transparent; }
  .block-container { padding-top: 1.6rem; max-width: 1280px; }
  h1 { letter-spacing: -0.01em; border-bottom: 2px solid #1F3864; padding-bottom: 0.35rem; }
  h2, h3 { color: #1F3864; }
  [data-testid="stMetricValue"] { color: #1F3864; }
  [data-testid="stMetricLabel"] p { font-size: 0.85rem; color: #4A5260; }
  .stTabs [data-baseweb="tab"] { font-weight: 600; }
  .rpdt-note { border-left: 3px solid #1F3864; background: #F3F5F8; padding: 0.6rem 0.9rem;
               margin: 0.4rem 0 1rem 0; font-size: 0.92rem; }
  .rpdt-meta { color: #4A5260; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

STATUS_STYLE = {"Green": "background-color:#DCEFE0", "Amber": "background-color:#FFF1C9",
                "Red": "background-color:#F8D7DA"}
PROSTATE_OPTIONS = ["Open surgery", "Robotic surgery at another centre"]
LT_TINTS = ["#E3EAF4", "#E6F0EA", "#F4ECE1", "#EDE6F2", "#F3E4E4", "#E2EFF1", "#F1F0DD", "#E9E9E9",
            "#E4E8EE", "#EFE6EA", "#E8EEE3"]


def gbp(x):
    if x is None:
        return "n/a"
    return f"-£{abs(x):,.0f}" if x < 0 else f"£{x:,.0f}"


def gbpm(x):
    return f"£{x / 1e6:,.2f}M"


def note(text):
    st.markdown(f'<div class="rpdt-note">{text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Reloading a saved case: values are placed in session state before widgets
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("load_count", 0)
ss.setdefault("grid_version", 0)
ss.setdefault("loaded_case", None)
if ss.get("pending_case") is not None:
    case_in = ss.pop("pending_case")
    for k, v in IO.widget_state(case_in).items():
        ss[k] = v
    c_in = case_in["configuration"]
    for f, v in c_in.get("platform_overrides", {}).items():
        if f == "instruments_per_case":
            ss[f"inst-{c_in['platform']}"] = float(v)
        elif f != "contract_volume_basis":
            ss[f"pf-{c_in['platform']}-{f}"] = float(v)
    ss["loaded_case"] = case_in
    ss["grid"] = copy.deepcopy(c_in.get("template")) if c_in.get("template") else None
    ss["grid_key"] = None
    ss["load_count"] += 1
    ss["grid_version"] += 1

defaults = dict(w_hospital=IO.HOSPITAL_LABELS["medium"], w_robots=1, w_platform="platform_b",
                w_price_mode="list", w_central=0, w_evidence="central", w_capvalue=False,
                w_prost=PROSTATE_OPTIONS[0], w_basis="per_robot", w_variant="standard",
                w_demandcheck=True, w_realisation=100)
for k, v in defaults.items():
    ss.setdefault(k, v)

# ---------------------------------------------------------------------------
# Sidebar: the decision being appraised
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Configuration")
up = st.sidebar.file_uploader("Reload a saved case (.json)", type=["json"])
if up is not None and ss.get("last_upload") != up.file_id:
    ss["last_upload"] = up.file_id
    parsed, err = IO.parse_case(up.getvalue())
    if err:
        st.sidebar.error(err)
    else:
        ss["pending_case"] = parsed
        st.rerun()

hospital = st.sidebar.radio("Hospital type", list(IO.HOSPITAL_LABELS.values()), key="w_hospital")
robots = st.sidebar.radio("Number of robots", [1, 2], horizontal=True, key="w_robots")
preset = ("medium_dgh_" if hospital.startswith("Medium") else "large_") + str(robots)
platform = st.sidebar.selectbox("Platform", list(D.PLATFORMS), key="w_platform",
                                format_func=lambda k: D.PLATFORMS[k]["label"])
pf_default = D.PLATFORMS[platform]
proc_set = pf_default.get("procedure_set", "multiport")
variant = st.sidebar.radio("Starting template", list(D.TEMPLATE_VARIANTS), key="w_variant",
                           format_func=lambda k: D.TEMPLATE_VARIANTS[k])
realisation = st.sidebar.number_input("Templated cases that go ahead (%)", min_value=50, max_value=100, step=1,
                                      key="w_realisation",
                                      help="Allows for cancellations and under-runs. 100% means every templated "
                                           "case goes ahead (placeholder).")

price_mode = st.sidebar.selectbox("Instrument price", ["list", "standard_discount", "volume_discount", "custom"],
                                  key="w_price_mode", format_func=lambda k: D.INSTRUMENT_PRICE_LABELS[k])
instrument_price = price_mode
if price_mode == "custom":
    ss.setdefault("w_quote", float(pf_default.get("instruments_per_case", 0)))
    instrument_price = st.sidebar.number_input("Trust quote: instruments per case (£)", min_value=0.0,
                                               step=50.0, key="w_quote")
central = 0
if pf_default["model"] == "purchase":
    central = st.sidebar.selectbox("Central capital per robot", D.CENTRAL_CAPITAL_OPTIONS, key="w_central",
                                   format_func=lambda v: "None (trust pays)" if v == 0 else f"£{v:,.0f}")
basis = None
if pf_default["model"] in ("managed_service", "per_procedure"):
    basis = st.sidebar.radio("Contract volumes apply", ["per_robot", "per_contract"], key="w_basis",
                             format_func=lambda k: D.CONTRACT_BASIS_LABELS[k].capitalize())
evidence = st.sidebar.selectbox("Clinical benefit setting", list(D.EVIDENCE_SETTINGS), key="w_evidence",
                                format_func=lambda k: D.EVIDENCE_LABELS[k])
prost = PROSTATE_OPTIONS[0]
if proc_set != "single_port" and preset.startswith("large"):
    prost = st.sidebar.radio("Prostatectomy comparator", PROSTATE_OPTIONS, key="w_prost")
capacity_value = st.sidebar.checkbox("Value released bed-days as extra elective activity", key="w_capvalue")
if pf_default.get("exploratory"):
    st.sidebar.warning("Exploratory platform: limited evidence, low UK use, illustrative price.")
st.sidebar.markdown(f'<p class="rpdt-meta">Engine version {D.ENGINE_VERSION}. Draft: assumptions awaiting '
                    'specialty review.</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Robotic Programme Decision Tool")
st.markdown('<p class="rpdt-meta">A 30-day cost-consequence tool to guardrail spending on robot-assisted '
            'surgery. It shows what an investment buys for patients and what it costs per outcome; it does not '
            'claim robots save money.</p>', unsafe_allow_html=True)
note("Draft. Every assumption is awaiting specialty review. Do not use the figures for approval until the "
     "assumptions register has been signed off.")

tab_in, tab_out, tab_sens, tab_bc = st.tabs(["Inputs", "Results", "Sensitivity and benchmark", "Business case"])

loaded = ss.get("loaded_case")
loaded_cfg = loaded["configuration"] if loaded else {}
same = loaded and loaded_cfg.get("preset") == preset and loaded_cfg.get("platform") == platform
loaded_groups = loaded_cfg.get("groups", {}) if same else {}
try:
    base_cfg = E.build_config(preset, platform, evidence, overrides={"groups": loaded_groups}, template=None)
except ValueError:
    base_cfg = E.build_config(preset, platform, evidence, template=None)
key_sfx = f"{preset}-{proc_set}-{ss['load_count']}"
proc_keys = T.procedure_keys(base_cfg)

# the template grid: regenerate when the starting point changes; a just-loaded
# case keeps its own template
grid_key = (preset, platform, robots, variant)
if ss.get("grid") is None or ss.get("grid_key") != grid_key:
    if ss.get("grid") is not None and ss.get("grid_key") is None:
        ss["grid"] = T.resize(ss["grid"], robots)
    else:
        ss["grid"] = T.suggest_template(dict(base_cfg, robots=robots), variant)
    ss["grid_version"] += 1
ss["grid_key"] = grid_key


def grid_to_df(robot_rows):
    return pd.DataFrame(T.to_ui_rows(base_cfg, robot_rows), columns=T.UI_COLUMNS)


def df_to_grid(df):
    return T.from_ui_rows(base_cfg, df.to_dict("records"))


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
with tab_in:
    st.subheader("Two-week theatre template")
    st.write("Fill in each robot's template as you would for a real two-week block: choose one procedure for "
             "each session, or leave it as 'Unfilled session'. The tool works out the cases from each procedure's "
             "complexity and extrapolates the fortnight to a year.")
    st.caption("Sessions 1 and 2 on weekdays are standard hours: an unfilled one is open but unbooked. Session 3 and "
               "weekend sessions count only when you book them. Friday session 2 is kept for maintenance. "
               "Whole-day procedures (radical cystectomy, liver, oesophagogastric and pancreatoduodenectomy) need "
               "both session 1 and session 2 of a day. Utilisation is booked sessions divided by available sessions.")
    opts = T.options(base_cfg)
    edited = []
    for rb in range(robots):
        rows = ss["grid"][rb] if rb < len(ss["grid"]) else T.empty_robot()
        st.markdown(f"**Robot {rb + 1}**")
        colcfg = {"Week": st.column_config.NumberColumn(disabled=True, width=60),
                  "Day": st.column_config.TextColumn(disabled=True, width=60)}
        for s_ in D.SESSIONS:
            colcfg[D.SESSION_LABELS[s_]] = st.column_config.SelectboxColumn(options=opts, required=True,
                                                                           width=320)
        df = st.data_editor(grid_to_df(rows), key=f"grid-{rb}-{ss['grid_version']}", hide_index=True,
                            width="stretch", height=36 * 15, column_config=colcfg, num_rows="fixed")
        edited.append(df_to_grid(df))
    grid_now = edited
    c1, c2 = st.columns([1, 3])
    if c1.button("Reset to the starting template"):
        ss["grid"] = T.suggest_template(dict(base_cfg, robots=robots), variant)
        ss["grid_version"] += 1
        st.rerun()

    with st.expander("Check against demand"):
        st.write("Annual robotic demand by procedure. When the check is on, delivered cases cannot exceed demand, "
                 "unmet demand is reported, and lists that demand cannot fill are flagged.")
        demand_check = st.checkbox("Check the template against demand", key="w_demandcheck")
        vol = pd.DataFrame([dict(group=k, Procedure=g["label"], **{"Annual demand": g["volume"]})
                            for k, g in base_cfg["groups"].items() if k not in D.NOT_MODELLED])
        vol_ed = st.data_editor(vol, key=f"vol-{key_sfx}", hide_index=True, width="stretch",
                                disabled=["group", "Procedure"],
                                column_config={"group": None, "Annual demand": st.column_config.NumberColumn(
                                    min_value=0, step=5)})
        st.caption(f"Above {D.PROGRAMME['max_cases_per_robot']:,} robotic operations per robot per year, across all "
                   "procedures, the tool shows an amber advisory guardrail; it does not cut activity.")
        if st.button("Suggest a template from this demand"):
            tmp = E.build_config(preset, platform, evidence, overrides={"robots": robots, "groups": {
                r["group"]: {"volume": float(r["Annual demand"])} for r in vol_ed.to_dict("records")}}, template=None)
            tmp["programme"]["realisation_factor"] = float(realisation) / 100
            ss["grid"] = T.suggest_template(tmp, variant)
            ss["grid_version"] += 1
            st.rerun()

    st.subheader("Platform prices")
    pf_over = {}
    fields = {"purchase": [("capital", "Capital per robot (£)"), ("trade_in", "Trade-in credit (£)"),
                           ("asset_life_years", "Asset life (years)"), ("maintenance_per_year", "Maintenance per robot per year (£)")],
              "managed_service": [("annual_fee", "Annual fee per robot (£)"), ("cases_included", "Cases included per year"),
                                  ("excess_fee_per_case", "Excess fee per case (£)")],
              "lease": [("lease_per_year", "Lease per robot per year (£)"), ("maintenance_per_year", "Maintenance per year (£)")],
              "per_procedure": [("fee_per_case", "Fee per case (£)"), ("minimum_cases_per_year", "Minimum cases per year")]}
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
        v = st.number_input("Instrument list price per case (£)", min_value=0.0, key=key)
        if v != pf_default.get("instruments_per_case", 0):
            pf_over["instruments_per_case"] = v
    if basis is not None and basis != pf_default.get("contract_volume_basis", "per_robot"):
        pf_over["contract_volume_basis"] = basis
    st.caption(f"Price basis: {pf_default['source']}")

    with st.expander("Tariff: extra income per robotic case (cash case only)"):
        st.write("Enter only the difference over what the trust would earn for the same patient without the robot. "
                 "Tariff is a transfer within the NHS: it reduces the trust's cash cost but is excluded from the "
                 "economic view and from cost per outcome.")
        tar = pd.DataFrame([dict(group=k, Procedure=g["label"], **{"Extra income per case (£)": g.get("tariff_uplift", 0.0),
                                                                  "Source": D.TARIFF_SOURCES.get(k, D.DEFAULT_TARIFF_SOURCE)})
                            for k, g in base_cfg["groups"].items() if k not in D.NOT_MODELLED])
        tar_ed = st.data_editor(tar, key=f"tariff-{key_sfx}", hide_index=True, width="stretch",
                                disabled=["group", "Procedure", "Source"],
                                column_config={"group": None, "Extra income per case (£)": st.column_config.NumberColumn(step=50)})

    with st.expander("Procedures: complexity and cases per session (advanced)"):
        st.write("Cases per session follow each procedure's complexity (High 1, Medium 1.5, Low 3; a whole-day "
                 "procedure 0.5, so one case across two sessions). Change them here; changes are flagged in every "
                 "output. Changing complexity or whole day resets cases per session to the default unless you "
                 "also change cases per session.")
        prow = [{"group": k, "Specialty": base_cfg["groups"][k]["specialty"], "Procedure": base_cfg["groups"][k]["label"],
                 "Complexity": base_cfg["groups"][k]["complexity"],
                 "Cases per session": float(base_cfg["groups"][k]["cases_per_session"]),
                 "Whole day": bool(base_cfg["groups"][k].get("whole_day")),
                 "30-day benefit": "Modelled" if base_cfg["groups"][k].get("benefit_modelled", True)
                 else "Not yet modelled"} for k in proc_keys]
        proc_ed = st.data_editor(pd.DataFrame(prow), key=f"procs-{key_sfx}", hide_index=True, width="stretch",
                                 disabled=["group", "Specialty", "Procedure", "30-day benefit"],
                                 column_config={"group": None,
                                                "Complexity": st.column_config.SelectboxColumn(
                                                    options=list(D.COMPLEXITY_CASES), required=True),
                                                "Cases per session": st.column_config.NumberColumn(
                                                    min_value=0.1, max_value=6.0, step=0.5),
                                                "Whole day": st.column_config.CheckboxColumn()})
        st.caption("'Not yet modelled' means the 30-day benefit is a zero placeholder pending evidence, not a "
                   "finding that the robot has no benefit.")

    with st.expander("Assumptions register for clinical review (Excel)"):
        st.write("Download the full register: one row per procedure and assumption, with value, source, evidence "
                 "grade and status, and columns for the reviewer's decision (agree, change to, needs evidence) and "
                 "comment. ID and Value are locked. Load the completed file to apply the changes.")
        st.download_button("Download the assumptions register (.xlsx)", RX.export(),
                           file_name=f"assumptions_register_v{D.ENGINE_VERSION}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        reg_up = st.file_uploader("Load a reviewed register (.xlsx)", type=["xlsx"], key="reg_upload")
        if reg_up is not None and ss.get("last_reg_upload") != reg_up.file_id:
            ss["last_reg_upload"] = reg_up.file_id
            ss["register_review"] = RX.load(reg_up.getvalue())
        review = ss.get("register_review")
        if review is None and loaded and loaded_cfg.get("register_review"):
            review = ss["register_review"] = loaded_cfg["register_review"]
        if review:
            st.write(f"Review loaded: {len(review['changes'])} changes applied, "
                     f"{len(review['needs_evidence'])} items marked 'needs evidence'.")
            for e in review.get("errors", []):
                st.warning(e)
            if st.button("Remove the loaded review"):
                ss["register_review"] = None
                st.rerun()

    with st.expander("Clinical assumptions at 30 days (advanced)"):
        st.write("Reductions per case, robotic versus each comparator. 'Share' is the proportion of these patients "
                 "who would have had that comparator without the robot.")
        pr_df = pd.DataFrame([r for r in E.prior_rows(base_cfg) if r["group"] not in D.NOT_MODELLED])
        pr_df["Without the robot"] = pr_df["comparator"].map(D.COMPARATOR_LABELS)
        pr_df = pr_df[["group", "comparator", "specialty", "Without the robot", "share", "los", "conv", "reop",
                       "comp", "readm", "extra_minutes"]]
        pr_ed = st.data_editor(pr_df, key=f"prior-{key_sfx}", width="stretch", hide_index=True,
                               disabled=["group", "comparator", "specialty", "Without the robot"],
                               column_config={"share": "Share", "los": "Bed-days saved", "conv": "Conversions avoided",
                                              "reop": "Returns to theatre avoided", "comp": "Complications avoided",
                                              "readm": "Readmissions avoided", "extra_minutes": "Extra minutes",
                                              "specialty": "Procedure", "group": None, "comparator": None})

# ---------------------------------------------------------------------------
# Assemble the configuration and run
# ---------------------------------------------------------------------------
group_over = {r["group"]: dict(volume=float(r["Annual demand"])) for r in vol_ed.to_dict("records")}
for r in tar_ed.to_dict("records"):
    if float(r["Extra income per case (£)"] or 0) != base_cfg["groups"][r["group"]].get("tariff_uplift", 0.0):
        group_over.setdefault(r["group"], {})["tariff_uplift"] = float(r["Extra income per case (£)"] or 0)
for k, o in E.overrides_from_prior_rows(pr_ed.to_dict("records"), platform).items():
    group_over.setdefault(k, {}).update(o)
if "prostatectomy" in group_over:
    if prost == PROSTATE_OPTIONS[1]:
        group_over["prostatectomy"].update(BC.PROSTATE_ELSEWHERE["prostatectomy"])
    elif group_over["prostatectomy"].get("p_robot_elsewhere", 0) >= 1:
        group_over["prostatectomy"].update(p_open=1.0, p_robot_elsewhere=0.0)
base_by_key = {k: base_cfg["groups"][k] for k in proc_keys}
for r_ in proc_ed.to_dict("records"):
    k, g0 = r_["group"], base_by_key[r_["group"]]
    o = {}
    cx, wd, cps = r_["Complexity"], bool(r_["Whole day"]), float(r_["Cases per session"] or 0)
    if cx != g0["complexity"]:
        o["complexity"] = cx
    if wd != bool(g0.get("whole_day")):
        o["whole_day"] = wd
    if o and cps == g0["cases_per_session"]:
        cps = D.default_cases_per_session(cx, wd)
    if cps != g0["cases_per_session"]:
        o["cases_per_session"] = cps
    if o:
        group_over.setdefault(k, {}).update(o)

configuration = dict(preset=preset, robots=robots, platform=platform, evidence=evidence,
                     instrument_price=instrument_price, central_capital_per_robot=central,
                     groups=group_over, platform_overrides=pf_over, template=grid_now, template_variant=variant,
                     demand_check=bool(demand_check), register_review=ss.get("register_review"),
                     programme=dict(include_capacity_value=capacity_value,
                                    realisation_factor=float(realisation) / 100))
try:
    kw = BC.configure(dict(configuration=configuration))
    res = E.run(E.build_config(**kw))
    error = None
except ValueError as exc:
    res, error = None, str(exc)

# ---------------------------------------------------------------------------
# Results: patient consequences, then cost per outcome, then five-year cost
# ---------------------------------------------------------------------------
with tab_out:
    if error:
        st.error(f"Input problem: {error}")
    else:
        cfg = res["config"]
        y3, t = res["yearly"][2], res["totals"]
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
                   "Neither 30-day cost avoided nor tariff income is deducted.")

        st.subheader("Five-year cost to the trust")
        c = st.columns(4)
        c[0].metric("Five-year extra cost (revenue)", gbpm(t["extra_cost"]))
        c[1].metric("Less extra tariff income", gbpm(t["tariff_income"]))
        c[2].metric("Net cash cost to the trust", gbpm(t["net_cash_cost"]))
        c[3].metric("Capital funded by the trust", gbp(res["capital"]["trust_funded"]))
        fy = pd.DataFrame([{"Year": y["year"], "Cases": f"{y['cases']:,.0f}", "Bed-days released": f"{y['bed_days']:,.0f}",
                            "Extra cost": gbp(y["extra_cost"]), "Tariff income": gbp(y["tariff_income"]),
                            "Net cash cost": gbp(y["net_cash_cost"]),
                            "30-day cost avoided (not cash)": gbp(y["offsets"])} for y in res["yearly"]])
        st.dataframe(fy, width="stretch", hide_index=True)
        st.caption(BC.TARIFF_NOTE + f" Net present cost to the NHS (economic view): {gbpm(res['economic']['net_present_cost'])}.")
        parts = []
        for y in res["yearly"]:
            for key, lab in [("platform_fixed", "Platform"), ("instruments", "Instruments"),
                             ("decontamination", "Sterile services"), ("staffing", "Surgical first assistant"),
                             ("theatre_time_cost", "Extra theatre time"), ("implementation", "Implementation and training"),
                             ("theatre_modification", "Theatre works")]:
                if y[key]:
                    parts.append(dict(Year=f"Year {y['year']}", Component=lab, Cost=y[key]))
        bars = alt.Chart(pd.DataFrame(parts)).mark_bar().encode(
            x=alt.X("Year:N", title=None), y=alt.Y("sum(Cost):Q", title="£"),
            color=alt.Color("Component:N", scale=alt.Scale(scheme="blues")))
        line = alt.Chart(pd.DataFrame([dict(Year=f"Year {y['year']}", Avoided=y["offsets"]) for y in res["yearly"]])
                         ).mark_line(point=True, color="#9B2226").encode(x="Year:N", y="Avoided:Q")
        st.altair_chart(bars + line, width="stretch")
        st.caption("Bars: extra cost to the trust. Line: 30-day cost avoided (not cash).")

        st.subheader("Break-even")
        be = res["break_even"]
        note(BC.break_even_sentence(be))

        st.subheader("Spending guardrails")
        g = pd.DataFrame([dict(Check=x["check"], Result=x["value"], Status=x["status"].capitalize(), Rule=x["rule"])
                          for x in res["guardrails"]])
        st.dataframe(g.style.map(lambda v: STATUS_STYLE.get(v, ""), subset=["Status"]), width="stretch",
                     hide_index=True)

        st.subheader("Theatre template: what it delivers")
        c = st.columns(3)
        c[0].metric("Sessions booked per fortnight", f"{res['booked_sessions_per_fortnight']:g} of "
                    f"{res['capacity_per_fortnight']:g}")
        c[1].metric("Robotic operations scheduled per year", f"{sum(g['planned_cases'] for g in res['groups'].values()):,.0f}")
        c[2].metric("Total unmet demand (cases a year)", f"{res['unmet_cases']:,.0f}")
        if res["unmet_cases"] >= 0.5:
            st.warning(f"{res['unmet_cases']:,.0f} cases a year of the demand entered cannot be scheduled. "
                       "See the warnings below for each procedure.")
        prow = []
        for k, go in res["groups"].items():
            if go.get("template_cases", 0) >= 0.5 or go["unmet_cases"] >= 0.5:
                prow.append({"Procedure": go["label"],
                             "30-day benefit": "Modelled" if go.get("benefit_modelled", True) else "Not yet modelled",
                             "Sessions per fortnight": round(go["sessions_per_fortnight"], 1),
                             "Cases on template (year)": round(go.get("template_cases", 0)),
                             "Cases delivered": round(go["planned_cases"]), "Unmet demand": round(go["unmet_cases"])})
        st.dataframe(pd.DataFrame(prow), width="stretch", hide_index=True)
        if res["input_mode"] == "template":
            tints = {k: LT_TINTS[i % len(LT_TINTS)] for i, k in enumerate(T.procedure_keys(cfg))}
            for rb in range(1, cfg["robots"] + 1):
                cells = [x for x in res["grid"] if x["robot"] == rb]
                table, colours = {}, {}
                for x in cells:
                    r_ = f"Week {x['week']} {x['day']}"
                    col = D.SESSION_LABELS[x["session"]]
                    table.setdefault(r_, {})[col] = BC.cell_text(cfg, x)
                    colours.setdefault(r_, {})[col] = tints.get(x["procedure"], "") if x["status"] == "booked" else ""
                cols = [D.SESSION_LABELS[s_] for s_ in D.SESSIONS]
                tdf = pd.DataFrame(table).T[cols]
                cdf = pd.DataFrame(colours).T[cols]
                st.markdown(f"**Robot {rb}**")
                st.dataframe(tdf.style.apply(lambda _: cdf.map(lambda v: f"background-color:{v}" if v else ""),
                                             axis=None), width="stretch", height=36 * 15)

        st.subheader("Instrument price targets (net of 30-day cost avoided)")
        pt = res["price_targets"]
        if pt["applicable"]:
            st.write(f"Current {gbp(pt['current_price'])} per case; needed for {gbp(pt['target_net_cost_per_bed_day'])} "
                     f"per bed-day released: {gbp(pt['price_for_target']) if pt['price_for_target'] is not None else 'not achievable'}; "
                     f"needed for budget neutrality: {gbp(pt['budget_neutral_price']) if pt['budget_neutral_price'] is not None else 'not achievable'}.")
        else:
            st.write(pt["note"])
        if res["warnings"]:
            st.subheader("Warnings")
            for w in res["warnings"]:
                st.warning(w)
        if res["user_modified"]:
            st.subheader("Assumptions changed from defaults")
            st.dataframe(pd.DataFrame([{"Assumption": E.describe_item(cfg, m["item"]), "Default": E.fmt_value(m["default"]),
                                        "Used": E.fmt_value(m["used"])} for m in res["user_modified"]]),
                         width="stretch", hide_index=True)
        with st.expander("Assumptions register"):
            st.dataframe(pd.DataFrame([{"Assumption": x["parameter"], "Value": x["value"], "Source": x["source"],
                                        "Status": x["status"], "Owner": x["owner"]} for x in RG.rows(cfg)]),
                         width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Sensitivity and benchmark
# ---------------------------------------------------------------------------
with tab_sens:
    if error:
        st.error("Fix the input problem first.")
    else:
        cfg = res["config"]
        st.subheader("One-way sensitivity")
        metric = st.selectbox("Result", list(S.METRICS), index=1, format_func=lambda k: S.METRICS[k][0])
        tor = S.tornado(cfg, metric, res)
        if tor["bars"]:
            rows = []
            for b in tor["bars"]:
                for lvl, lab in (("low", b["low_label"]), ("high", b["high_label"])):
                    rows.append(dict(Assumption=b["name"], Setting=f"{lvl.capitalize()}: {lab}", Level=lvl.capitalize(),
                                     start=tor["base"], end=b[lvl], swing=b["swing"]))
            df = pd.DataFrame(rows)
            order = [b["name"] for b in tor["bars"]]
            chart = alt.Chart(df).mark_bar().encode(
                y=alt.Y("Assumption:N", sort=order, title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X("start:Q", title=tor["metric_label"] + " (£)"), x2="end:Q",
                color=alt.Color("Level:N", scale=alt.Scale(domain=["Low", "High"], range=["#7FA7C9", "#1F3864"])),
                tooltip=["Assumption", "Setting", alt.Tooltip("end:Q", format=",.0f")])
            rule = alt.Chart(pd.DataFrame([{"base": tor["base"]}])).mark_rule(color="#6B7280").encode(x="base:Q")
            st.altair_chart((chart + rule).properties(height=36 * len(order) + 40), width="stretch")
            st.caption(f"Base case {gbp(tor['base'])}. Each assumption is moved on its own; the template is held fixed. "
                       "Ranges are placeholders for expert review."
                       + (f" No effect on this result: {', '.join(tor['no_effect']).lower()}." if tor["no_effect"] else ""))
        if proc_set != "single_port":
            st.subheader("Comparison with a benchmark programme")
            bench = BM.run_benchmark(cfg)
            st.dataframe(pd.DataFrame([dict(Measure=a, **{"This proposal": b, "Benchmark": c, "Benchmark source": d})
                                       for a, b, c, d in BM.comparison_rows(res, bench)]), width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Business case
# ---------------------------------------------------------------------------
with tab_bc:
    st.subheader("Business case")
    st.write("The Word business case is the main output: a Five Case Model document built from these inputs.")
    c = st.columns(2)
    cover_defaults = dict(trust_name="[Trust name]", prepared_by="[Name, role]", sro="[Name, role]",
                          clinical_lead="[Name, role]", finance_lead="[Name, role]", version="Draft 0.1",
                          status=BC.DRAFT_STATUS, date=date.today().strftime("%d %B %Y"))
    labels = dict(trust_name="Trust name", prepared_by="Prepared by", sro="Senior responsible owner",
                  clinical_lead="Clinical lead", finance_lead="Finance lead", version="Version", status="Status", date="Date")
    cover = {}
    for i, f in enumerate(IO.COVER_FIELDS):
        ss.setdefault(f"c_{f}", cover_defaults[f])
        cover[f] = c[i % 2].text_input(labels[f], key=f"c_{f}")
    case = dict(cover=cover, configuration=configuration)
    if error:
        st.error("Fix the input problem before generating the business case.")
    elif st.button("Generate Word business case", type="primary"):
        with st.spinner("Building the business case"):
            data, _ = BC.build_docx_bytes(case)
        name = "".join(ch for ch in cover["trust_name"] if ch.isalnum() or ch in " -_").strip() or "Trust"
        st.download_button("Download business case (.docx)", data, file_name=f"Robotic_business_case_{name}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.download_button("Save these inputs (.json) to reload this case later", json.dumps(case, indent=1),
                       file_name="robotic_case_inputs.json", mime="application/json")
    st.caption("The tool does not store anything you enter. Save the inputs file and reload it from the sidebar.")
