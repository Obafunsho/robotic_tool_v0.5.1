"""
Robotic Programme Decision Tool: web interface.

Run locally:   streamlit run app.py
All calculations come from engine.py; the Word document from business_case.py.
No data entered here is stored on the server. A case can be saved as an inputs
file (.json) and reloaded later.
"""
import json
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

import benchmark as BM
import business_case as BC
import defaults as D
import engine as E
import inputs_io as IO
import register as RG
import sensitivity as S

st.set_page_config(page_title="Robotic Programme Decision Tool", layout="wide")

LIST_LABELS = {1: "Half day", 2: "All day"}
STATUS_STYLE = {"Green": "background-color:#C6EFCE", "Amber": "background-color:#FFEB9C",
                "Red": "background-color:#FFC7CE"}
PROSTATE_OPTIONS = ["Open surgery", "Robotic surgery at another centre"]


def gbp(x):
    if x is None:
        return "n/a"
    return f"-£{abs(x):,.0f}" if x < 0 else f"£{x:,.0f}"


def gbpm(x):
    return f"£{x / 1e6:,.2f}M"


# ---------------------------------------------------------------------------
# Reloading a saved case: values are placed in session state before any
# widget is drawn, so every input starts from the saved case.
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("load_count", 0)
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
    ss["load_count"] += 1

defaults = dict(w_hospital=IO.HOSPITAL_LABELS["medium"], w_robots=1, w_platform="platform_b",
                w_price_mode="list", w_central=0, w_evidence="central", w_capvalue=False,
                w_prost=PROSTATE_OPTIONS[0], w_basis="per_robot")
for k, v in defaults.items():
    ss.setdefault(k, v)

# ---------------------------------------------------------------------------
# Sidebar: the decision being appraised
# ---------------------------------------------------------------------------
st.sidebar.header("Configuration")
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
else:
    st.sidebar.caption("Central capital applies to purchase models only.")

basis = None
if pf_default["model"] in ("managed_service", "per_procedure"):
    basis = st.sidebar.radio("Contract volumes apply", ["per_robot", "per_contract"], key="w_basis",
                             format_func=lambda k: D.CONTRACT_BASIS_LABELS[k].capitalize())

evidence = st.sidebar.selectbox("Clinical benefit setting", list(D.EVIDENCE_SETTINGS), key="w_evidence",
                                format_func=lambda k: D.EVIDENCE_LABELS[k])
prost = PROSTATE_OPTIONS[0]
if proc_set != "single_port" and preset.startswith("large"):
    prost = st.sidebar.radio("Prostatectomy comparator", PROSTATE_OPTIONS, key="w_prost",
                             help="Open surgery is the default. Robotic surgery at another centre is a sensitivity "
                                  "scenario with no 30-day difference.")
capacity_value = st.sidebar.checkbox("Value released bed-days as extra elective activity", key="w_capvalue")

if pf_default.get("exploratory"):
    st.sidebar.warning("Exploratory platform: limited evidence, low UK use, illustrative price.")

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
st.title("Robotic Programme Decision Tool")
st.caption("A 30-day cost-consequence tool to guardrail spending on robot-assisted surgery. It shows what an "
           "investment buys for patients and what it costs per outcome. It does not claim robots save money.")
st.warning("Draft: every assumption is awaiting specialty review. Do not use the figures for approval until the "
           "assumptions register has been signed off.")

tab_in, tab_out, tab_sens, tab_bc = st.tabs(["1. Inputs", "2. Results", "3. Sensitivity and benchmark",
                                             "4. Business case"])
loaded = ss.get("loaded_case")
loaded_groups = {}
if loaded and loaded["configuration"]["preset"] == preset and loaded["configuration"]["platform"] == platform:
    loaded_groups = loaded["configuration"].get("groups", {})
try:
    base_cfg = E.build_config(preset, platform, evidence, overrides={"groups": loaded_groups})
except ValueError:
    base_cfg = E.build_config(preset, platform, evidence)
key_sfx = f"{preset}-{proc_set}-{ss['load_count']}"

with tab_in:
    st.subheader("Case volumes and lists")
    st.write("Annual robotic cases available for each specialty (demand). Set to 0 if the trust does not do it.")
    st.caption(f"The cap of {D.PROGRAMME['max_cases_per_robot']:,} applies to the total robotic operations delivered "
               "per robot per year across all specialties, not to any single entry here: you can enter more demand "
               "than the robot can deliver, and the excess is reported as unmet demand. In practice theatre sessions "
               "usually limit volume before the cap does; the cap only binds when lists hold many short cases.")
    vol = pd.DataFrame([dict(group=k, Specialty=g["label"], **{"Robotic cases per year": g["volume"],
                                                                "Cases per list": g["cases_per_list"],
                                                                "List length": LIST_LABELS[g["list_sessions"]]})
                        for k, g in base_cfg["groups"].items()])
    vol_ed = st.data_editor(vol, key=f"vol-{key_sfx}", width="stretch", hide_index=True,
                            disabled=["group", "Specialty"],
                            column_config={"group": None, "List length": st.column_config.SelectboxColumn(options=list(LIST_LABELS.values())),
                                           "Robotic cases per year": st.column_config.NumberColumn(min_value=0, step=5),
                                           "Cases per list": st.column_config.NumberColumn(min_value=1, step=1)})

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

    with st.expander("Clinical assumptions at 30 days (advanced)"):
        st.write("Reductions per case, robotic versus each comparator. 'Share' is the proportion of these patients "
                 "who would have had that comparator without the robot. Changed values are flagged in every output.")
        pr_df = pd.DataFrame(E.prior_rows(base_cfg))
        pr_df["Without the robot"] = pr_df["comparator"].map(D.COMPARATOR_LABELS)
        pr_df = pr_df[["group", "comparator", "specialty", "Without the robot", "share", "los", "conv", "reop",
                       "comp", "readm", "extra_minutes"]]
        pr_ed = st.data_editor(pr_df, key=f"prior-{key_sfx}", width="stretch", hide_index=True,
                               disabled=["group", "comparator", "specialty", "Without the robot"],
                               column_config={"share": "Share", "los": "Bed-days saved", "conv": "Conversions avoided",
                                              "reop": "Returns to theatre avoided", "comp": "Complications avoided",
                                              "readm": "Readmissions avoided", "extra_minutes": "Extra minutes",
                                              "specialty": "Specialty", "group": None, "comparator": None})
        if proc_set != "single_port":
            st.caption("For multi-port specialties, the open share sets the split; the laparoscopic share is derived.")

# ---------------------------------------------------------------------------
# Assemble overrides and run
# ---------------------------------------------------------------------------
inv = {v: k for k, v in LIST_LABELS.items()}
group_over = {r["group"]: dict(volume=float(r["Robotic cases per year"]), cases_per_list=float(r["Cases per list"]),
                               list_sessions=inv[r["List length"]]) for r in vol_ed.to_dict("records")}
for k, o in E.overrides_from_prior_rows(pr_ed.to_dict("records"), platform).items():
    group_over.setdefault(k, {}).update(o)
if "prostatectomy" in group_over:
    if prost == PROSTATE_OPTIONS[1]:
        group_over["prostatectomy"].update(BC.PROSTATE_ELSEWHERE["prostatectomy"])
    elif group_over["prostatectomy"].get("p_robot_elsewhere", 0) >= 1:
        group_over["prostatectomy"].update(p_open=1.0, p_robot_elsewhere=0.0)

configuration = dict(preset=preset, robots=robots, platform=platform, evidence=evidence,
                     instrument_price=instrument_price, central_capital_per_robot=central,
                     groups=group_over, platform_overrides=pf_over,
                     programme=dict(include_capacity_value=capacity_value))
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

        st.subheader("Cost per outcome (five years)")
        c = st.columns(4)
        c[0].metric("Extra cost per operation", gbp(t["cost_per_case"]))
        c[1].metric("Extra cost per open operation avoided", gbp(t["cost_per_open_operation_avoided"]))
        c[2].metric("Extra cost per bed-day released", gbp(t["cost_per_bed_day_released"]))
        c[3].metric("Extra cost per serious event avoided", gbp(t["cost_per_serious_event_avoided"]))
        st.caption("Each ratio divides the whole five-year extra cost by one consequence; they must not be added. "
                   "No 30-day cost avoided is deducted.")

        st.subheader("Five-year cost to the trust")
        c = st.columns(3)
        c[0].metric("Five-year extra cost (revenue)", gbpm(t["extra_cost"]))
        c[1].metric("Capital funded by the trust", gbp(res["capital"]["trust_funded"]))
        c[2].metric("Net present cost to the NHS (economic)", gbpm(res["economic"]["net_present_cost"]))
        fy = pd.DataFrame([{"Year": y["year"], "Cases": f"{y['cases']:,.0f}", "Bed-days released": f"{y['bed_days']:,.0f}",
                            "Extra cost": gbp(y["extra_cost"]), "30-day cost avoided (not cash)": gbp(y["offsets"]),
                            "Extra cost less cost avoided": gbp(y["net_cost"])} for y in res["yearly"]])
        st.dataframe(fy, width="stretch", hide_index=True)
        st.caption("Revenue cost includes depreciation and public dividend capital on trust-funded capital, so capital "
                   "and revenue must not be added. Cost avoided releases capacity, not cash.")
        parts = []
        for y in res["yearly"]:
            for key, lab in [("platform_fixed", "Platform"), ("instruments", "Instruments"),
                             ("decontamination", "Sterile services"), ("staffing", "Surgical first assistant"),
                             ("theatre_time_cost", "Extra theatre time"), ("implementation", "Implementation and training"),
                             ("theatre_modification", "Theatre works")]:
                if y[key]:
                    parts.append(dict(Year=f"Year {y['year']}", Component=lab, Cost=y[key]))
        bars = alt.Chart(pd.DataFrame(parts)).mark_bar().encode(
            x=alt.X("Year:N", title=None), y=alt.Y("sum(Cost):Q", title="£"), color=alt.Color("Component:N"))
        line = alt.Chart(pd.DataFrame([dict(Year=f"Year {y['year']}", Avoided=y["offsets"]) for y in res["yearly"]])
                         ).mark_line(point=True, color="#C00000").encode(x="Year:N", y="Avoided:Q")
        st.altair_chart(bars + line, width="stretch")
        st.caption("Bars: extra cost to the trust. Red line: 30-day cost avoided (not cash).")

        st.subheader("Break-even")
        be = res["break_even"]
        (st.success if be["status"] in ("within_capacity", "already") else st.info)(BC.break_even_sentence(be))
        if be.get("max_cases"):
            st.caption(f"Searched only up to the maximum deliverable volume of about {be['max_cases']:,.0f} cases a year "
                       f"(cap {D.PROGRAMME['max_cases_per_robot']:,} per robot, or every session filled).")

        st.subheader("Spending guardrails")
        g = pd.DataFrame([dict(Check=x["check"], Result=x["value"], Status=x["status"].capitalize(), Rule=x["rule"])
                          for x in res["guardrails"]])
        st.dataframe(g.style.map(lambda v: STATUS_STYLE.get(v, ""), subset=["Status"]), width="stretch",
                     hide_index=True)

        st.subheader("Fortnightly list plan")
        c = st.columns(3)
        c[0].metric("Sessions booked per fortnight", f"{res['booked_sessions_per_fortnight']:g} of {res['capacity_per_fortnight']}")
        c[1].metric("Robotic operations scheduled per year", f"{sum(g['planned_cases'] for g in res['groups'].values()):,.0f}")
        c[2].metric("Total unmet demand (cases a year)", f"{res['unmet_cases']:,.0f}")
        if res["unmet_cases"] >= 0.5:
            st.warning(f"{res['unmet_cases']:,.0f} cases a year of the demand entered cannot be scheduled. "
                       "See the warnings below for each specialty.")
        st.write(f"{res['booked_sessions_per_fortnight']:g} of {res['capacity_per_fortnight']} sessions booked "
                 f"({res['booked_utilisation']:.0%}); {res['spare_sessions_per_fortnight']:g} free. Robots needed for full "
                 f"demand: {res['robots_needed']['fractional']:.2f}. Lists are created only if at least "
                 f"{D.PROGRAMME['min_list_fill']:.0%} full; smaller demand is pooled on a shared list.")
        plan_rows = []
        for k, v in res["plan"].items():
            if k == E.SHARED:
                continue
            go = res["groups"][k]
            if v or go["shared_cases"] >= 0.5 or go["unmet_cases"] >= 0.5:
                plan_rows.append({"Specialty": go["label"], "Sessions per fortnight": v,
                                  "Cases on own lists": round(go["dedicated_cases"]),
                                  "Cases on shared list": round(go["shared_cases"]), "Unmet demand": round(go["unmet_cases"])})
        if res["plan"].get(E.SHARED):
            plan_rows.append({"Specialty": E.shared_label(), "Sessions per fortnight": res["plan"][E.SHARED],
                              "Cases on own lists": 0,
                              "Cases on shared list": round(sum(x["shared_cases"] for x in res["groups"].values())),
                              "Unmet demand": 0})
        st.dataframe(pd.DataFrame(plan_rows), width="stretch", hide_index=True)
        for rb in range(1, cfg["robots"] + 1):
            grid = {}
            for x in res["grid"]:
                if x["robot"] == rb:
                    grid.setdefault(f"Week {x['week']} {x['session']}", {})[x["day"]] = (
                        E.slot_label(cfg, x["group"]) if x["group"] else "Unbooked")
            st.write(f"Robot {rb}")
            st.dataframe(pd.DataFrame(grid).T.reindex(columns=["Mon", "Tue", "Wed", "Thu", "Fri"]).fillna("Maintenance"),
                         width="stretch")

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
            st.dataframe(pd.DataFrame([{"Assumption": E.describe_item(cfg, m["item"]), "Default": f"{m['default']:g}",
                                        "Used": f"{m['used']:g}"} for m in res["user_modified"]]),
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
        st.subheader("One-way sensitivity (tornado)")
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
                y=alt.Y("Assumption:N", sort=order, title=None, axis=alt.Axis(labelLimit=0)), x=alt.X("start:Q", title=tor["metric_label"] + " (£)"),
                x2="end:Q", color=alt.Color("Level:N", scale=alt.Scale(domain=["Low", "High"], range=["#2E8B8B", "#1F3864"])),
                tooltip=["Assumption", "Setting", alt.Tooltip("end:Q", format=",.0f")])
            rule = alt.Chart(pd.DataFrame([{"base": tor["base"]}])).mark_rule(color="grey").encode(x="base:Q")
            st.altair_chart((chart + rule).properties(height=36 * len(order) + 40), width="stretch")
            st.caption(f"Base case {gbp(tor['base'])}. Each assumption is moved on its own; the list plan is held fixed. "
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
    st.subheader("Cover page")
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
