"""
Build an NHS Five Case Model business case from engine outputs.

Usage:
  python3 business_case.py case.json out.docx

case.json holds the cover-page details and the chosen configuration (see
examples/example_case.json). Content is assembled here as simple blocks and
rendered to Word by docx_render.py (python-docx), so the wording can be tested
without Word. Square-bracketed text, e.g. [Trust name], is highlighted in the
document for the trust to complete.

Order of every summary (fixed): patient consequences first, then cost per
outcome, then five-year cost. The headline cost is the extra cost to the trust
with no deduction for bed-days or any other 30-day cost avoided.
"""
import copy
import json
import sys
from datetime import date
from pathlib import Path

import benchmark as BM
import charts
import defaults as D
import docx_render
import engine as E
import register as RG
import sensitivity as S
import templates as T

HERE = Path(__file__).parent
DRAFT_STATUS = "Draft: assumptions awaiting specialty review"


def gbp(x, dp=0):
    if x is None:
        return "not achievable"
    sign = "-" if x < 0 else ""
    return f"{sign}£{abs(x):,.{dp}f}"


def ratio(x):
    return "n/a" if x is None else gbp(x)


def gbpm(x):
    sign = "-" if x < 0 else ""
    return f"{sign}£{abs(x) / 1e6:,.2f}M"


def gbpk(x):
    return f"{x / 1e3:,.0f}"


def n0(x):
    return f"{x:,.0f}"


def n1(x):
    return f"{x:,.1f}"


def plural(n, word):
    return f"{n} {word}{'s' if n != 1 else ''}"


# ---------------------------------------------------------------------------
def configure(case):
    c = case["configuration"]
    ov = {"programme": {"central_capital_per_robot": c.get("central_capital_per_robot", 0)},
          "robots": c["robots"]}
    for k, src in (("groups", "groups"), ("unit_costs", "unit_costs"), ("platform", "platform_overrides")):
        if src in c:
            ov[k] = copy.deepcopy(c[src])
    for k, v in c.get("programme", {}).items():
        ov["programme"][k] = v
    if "list_map" in c:
        ov["list_map"] = copy.deepcopy(c["list_map"])
    if "demand_check" in c:
        ov["demand_check"] = bool(c["demand_check"])
    template = c.get("template") or c.get("template_variant", "standard")
    if c.get("plan") is not None:
        template = None
    return dict(preset=c["preset"], platform=c["platform"], evidence=c.get("evidence", "central"),
                overrides=ov, instrument_price=c.get("instrument_price", "list"),
                plan=c.get("plan"), template=template)


def with_changes(base, **changes):
    """A copy of build_config keyword arguments with the given changes applied.
    group_overrides = {group: {field: value}} is merged into the case's own."""
    kw = json.loads(json.dumps(base))
    for k, v in changes.items():
        if k == "robots":
            if kw["overrides"].get("robots") != v and isinstance(kw.get("template"), list):
                # a custom template is drawn for one robot count: other counts use a
                # template suggested from demand
                kw["template"] = "standard"
            kw["overrides"]["robots"] = v
            kw["plan"] = None
        elif k == "central_capital_per_robot":
            kw["overrides"]["programme"]["central_capital_per_robot"] = v
        elif k == "group_overrides":
            g = kw["overrides"].setdefault("groups", {})
            for gk, fields in v.items():
                g.setdefault(gk, {}).update(fields)
        elif k == "platform":
            kw["platform"] = v
            # platform-specific quotes do not carry over to another platform
            kw["overrides"].pop("platform", None)
            if isinstance(kw.get("instrument_price"), (int, float)):
                kw["instrument_price"] = "list"
        else:
            kw[k] = v
    return kw


def run_with(base, **changes):
    return E.run(E.build_config(**with_changes(base, **changes)))


PROSTATE_ELSEWHERE = {"prostatectomy": {"p_open": 0.0, "p_robot_elsewhere": 1.0}}


def recommended_robots(base):
    """Largest robot count (1 or 2) whose booked utilisation is at least 75%."""
    best = 1
    for n in (1, 2):
        if run_with(base, robots=n)["booked_utilisation"] >= D.PROGRAMME["low_utilisation_warning"]:
            best = n
    return best


def break_even_sentence(be):
    if be["status"] == "within_capacity":
        return (f"Break-even: 30-day cost avoided would cover the extra cost at about "
                f"{n0(be['break_even_cases'])} cases a year, within the maximum of about {n0(be['max_cases'])}.")
    if be["status"] == "beyond_capacity":
        return (f"Break-even: not reachable within capacity. Even at the maximum of about {n0(be['max_cases'])} "
                f"cases a year, 30-day cost avoided would fall short of the extra cost by about "
                f"{gbp(be['net_cost_at_max'])} a year.")
    if be["status"] == "already":
        return "Break-even: 30-day cost avoided already covers the extra cost at the planned volume."
    if be["status"] == "none":
        return ("Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, "
                "so higher volume lowers the cost per case but never reaches break-even.")
    return "Break-even: not applicable (no robotic cases planned)."


def label_for(cfg, key):
    return E.slot_label(cfg, key, short=False)


def n_lists_txt(r):
    if r["input_mode"] == "template":
        n = len(r["template_summary"]["list_type_sessions"])
        return plural(n, "list type") + " on the two-week theatre template"
    n = sum(1 for k, v in r["plan"].items() if v and k != E.SHARED)
    return plural(n, "specialty").replace("specialtys", "specialties") + (
        " and a shared list" if r["plan"].get(E.SHARED) else "")


def scheduled_groups(r):
    return [k for k, g in r["groups"].items() if g["planned_cases"] >= 0.5 and k not in D.NOT_MODELLED]


# ---------------------------------------------------------------------------
def build_blocks(case, include_charts=True):
    base = configure(case)
    r = E.run(E.build_config(**base))
    cfg = r["config"]
    cov = case.get("cover", {})
    trust = cov.get("trust_name", "[Trust name]")
    pf = cfg["platform"]
    pr = cfg["programme"]
    y3 = r["yearly"][min(3, len(r["yearly"])) - 1]
    t = r["totals"]
    H = pr["horizon_years"]
    inj = pr["central_capital_per_robot"]
    rec = recommended_robots(base)
    bench = BM.run_benchmark(cfg) if pf.get("procedure_set") != "single_port" else None
    reg = RG.rows(cfg)
    reg_open = sum(1 for x in reg if x["status"] != "Sourced")
    B = []
    add = B.append
    robots_txt = plural(cfg["robots"], "robot")

    # Cover -------------------------------------------------------------------
    add(dict(type="cover", title=cov.get("title", "Business case: robot-assisted surgery programme"),
             subtitle=f"{robots_txt}, {pf['label']}", trust=trust, fields=[
                 ("Prepared by", cov.get("prepared_by", "[Name, role]")),
                 ("Senior responsible owner", cov.get("sro", "[Name, role]")),
                 ("Clinical lead", cov.get("clinical_lead", "[Name, role]")),
                 ("Finance lead", cov.get("finance_lead", "[Name, role]")),
                 ("Date", cov.get("date", date.today().strftime("%d %B %Y"))),
                 ("Version", cov.get("version", "Draft 0.1")),
                 ("Status", cov.get("status", DRAFT_STATUS)),
             ],
             footnote=(f"DRAFT. Generated by the Robotic Programme Decision Tool, engine version {cfg['version']}. "
                       f"{reg_open} of the {len(reg)} assumptions in the register (Appendix D) are placeholders, "
                       "assumptions or only partly sourced, and none has yet been reviewed by the relevant specialty. "
                       "The figures must not be used for approval until that review is complete.")))
    add(dict(type="toc"))
    add(dict(type="pagebreak"))

    # 1 Executive summary --------------------------------------------------------
    add(dict(type="h1", text="1. Executive summary"))
    add(dict(type="p", text=(
        f"This business case seeks approval for a robot-assisted surgery programme at {trust}: "
        f"{robots_txt} ({pf['label'].split(':')[0]}), operating {r['booked_sessions_per_fortnight']:g} of "
        f"{r['capacity_per_fortnight']:g} available sessions per fortnight across "
        f"{n_lists_txt(r)}.")))
    add(dict(type="p", text=(
        "It is presented as an investment in quality, access and capacity, not as a cost-saving proposal. "
        "The case sets out first what the investment buys for patients, then what it costs per outcome, "
        "then the extra cost to the trust over five years, and the guardrails that keep spending efficient.")))
    if pf.get("exploratory"):
        add(dict(type="p", text=(
            "This platform is exploratory. Comparative evidence is limited and mostly from outside the UK, UK "
            "use is low, and the price used is illustrative. The figures below are indicative only.")))
    add(dict(type="h3", text="What the programme delivers for patients each year (year 3, steady state)"))
    add(dict(type="table", header=["Patient consequence", "Number per year"], widths=[6500, 2526],
             rows=[["Robotic operations", n0(y3["cases"])],
                   ["Open operations avoided", n0(y3["open_avoided"])],
                   ["Bed-days released", n0(y3["bed_days"])],
                   ["Conversions to open surgery avoided", n1(y3["conversions"])],
                   ["Major complications avoided", n1(y3["complications"])],
                   ["Returns to theatre avoided", n1(y3["reoperations"])],
                   ["Readmissions avoided", n1(y3["readmissions"])],
                   ["Extra elective operations the released beds could support", n0(y3["extra_elective_cases_enabled"])]]))
    add(dict(type="h3", text="Cost per outcome (five years)"))
    add(dict(type="table", header=["Measure", "Extra cost to the trust"], widths=[6500, 2526], rows=[
        ["Per robotic operation", ratio(t["cost_per_case"])],
        ["Per open operation avoided", ratio(t["cost_per_open_operation_avoided"])],
        ["Per bed-day released", ratio(t["cost_per_bed_day_released"])],
        ["Per serious event avoided (complication, return to theatre or readmission)",
         ratio(t["cost_per_serious_event_avoided"])]]))
    add(dict(type="p", text=(
        "Each ratio divides the whole five-year extra cost by one consequence, so they must not be added. "
        "Neither 30-day cost avoided nor tariff income is deducted, so the ratios measure NHS resources used.")))
    add(dict(type="h3", text="Five-year cost to the trust"))
    hdr = ["£ (thousands)"] + [f"Year {y['year']}" for y in r["yearly"]] + ["Total"]
    rows5 = [["Extra cost to the trust (revenue)"] + [gbpk(y["extra_cost"]) for y in r["yearly"]]
             + [gbpk(t["extra_cost"])]]
    if t["tariff_income"]:
        rows5 += [["Less extra tariff income"] + [gbpk(-y["tariff_income"]) for y in r["yearly"]]
                  + [gbpk(-t["tariff_income"])],
                  ["Net cash cost to the trust"] + [gbpk(y["net_cash_cost"]) for y in r["yearly"]]
                  + [gbpk(t["net_cash_cost"])]]
    add(dict(type="table", header=hdr, widths=[2626] + [1067] * 5 + [1065], rows=rows5, bold_last=True))
    add(dict(type="p", text=TARIFF_NOTE + (
        "" if t["tariff_income"] else " No extra tariff income has been entered for this case.")))
    cap = r["capital"]
    if pf["model"] == "purchase":
        add(dict(type="p", text=(
            f"Capital: {gbp(cap['total'])} in total, of which {gbp(cap['trust_funded'])} is funded by the trust "
            f"and {gbp(cap['central'])} is assumed from central funds. Revenue cost includes depreciation and "
            "public dividend capital on the trust-funded capital, so capital and revenue must not be added.")))
    add(dict(type="p", text=(
        f"Over five years the programme would also avoid about {gbp(t['offsets'])} of 30-day costs, mostly "
        f"bed-days ({n0(t['bed_days'])}). These are not deducted: they release capacity, not cash, unless beds or "
        "staff are removed or reused. They are shown in the economic case.")))
    add(dict(type="p", text=break_even_sentence(r["break_even"])))
    if bench is not None:
        add(dict(type="p", text=(
            f"For comparison, a well-functioning benchmark programme (about {D.BENCHMARK['cases_per_robot']} cases per "
            f"robot a year, typical case mix, mid-level costs) would cost about {ratio(bench['totals']['cost_per_case'])} "
            f"per robotic operation and {ratio(bench['totals']['cost_per_bed_day_released'])} per bed-day released, "
            f"against {ratio(t['cost_per_case'])} and {ratio(t['cost_per_bed_day_released'])} here (section 3.4).")))
    add(dict(type="h3", text="Spending guardrails"))
    add(dict(type="table", header=["Check", "Result", "Status"], widths=[5000, 2200, 1826],
             rows=[[g["check"], g["value"], g["status"].capitalize()] for g in r["guardrails"]], status_col=2))
    if rec != cfg["robots"]:
        add(dict(type="p", text=(
            f"The tool's utilisation rule recommends {plural(rec, 'robot')} for this case mix, which differs from "
            f"the {cfg['robots']} proposed. The board should be satisfied that the additional capacity will be "
            "filled before approving.")))
    add(dict(type="h3", text="Recommendation"))
    instr_txt = (f", an instrument price no higher than {gbp(pf['instruments_per_case'])} per case"
                 if pf.get("instruments_per_case") and not pf.get("instruments_included") else "")
    add(dict(type="p", text=(
        "[Board recommendation to be completed by the senior responsible owner.] The board is asked to approve "
        f"the preferred option subject to completion of the specialty review of assumptions, a formal price "
        f"quote{instr_txt}, and a benefits realisation review at 12 months.")))
    add(dict(type="pagebreak"))

    # 2 Strategic case ---------------------------------------------------------------
    add(dict(type="h1", text="2. Strategic case"))
    add(dict(type="h2", text="2.1 Case for change"))
    add(dict(type="p", text=(
        f"[Describe {trust}'s current position: surgical waiting lists, current minimal access rates by "
        "specialty, workforce and training needs, and any existing robotic provision.]")))
    add(dict(type="p", text=(
        "Robot-assisted surgery is expanding across the NHS. NICE's early value assessment of robot-assisted "
        "surgery for soft tissue procedures (HTE21, April 2025) allows these systems to be used while further "
        "evidence is generated, and asks centres to collect data on costs, activity, conversion to open surgery, "
        "rates of minimal access surgery and outcomes. Robotic prostatectomy was outside its scope because it is "
        "established NHS practice. This programme commits to that data collection through its 12-month review.")))
    add(dict(type="p", text=(
        "National implementation guidance from NHS England and GIRFT (July 2025) asks that robotic programmes be "
        "high volume and fully used on all working days, approved through a full business case with regional "
        "stakeholders, overseen by a steering committee, and planned with capital replacement in mind. It also says "
        "that provision for recruiting and training surgical first assistants or surgical care practitioners should "
        "be built into the business case. This case is structured to follow that guidance.")))
    add(dict(type="h2", text="2.2 Specialties and priorities"))
    sg = scheduled_groups(r)
    pri = [cfg["groups"][k]["label"] for k in sg if cfg["groups"][k]["nhse_priority"]]
    oth = [cfg["groups"][k]["label"] for k in sg if not cfg["groups"][k]["nhse_priority"]]
    sh = [g["label"] for k, g in r["groups"].items() if g["shared_cases"] >= 0.5]
    add(dict(type="p", text=(
        "The programme includes specialties that NHS England has signalled as priorities for robotic access: "
        f"{', '.join(pri) if pri else 'none scheduled in this configuration'}. Other procedures scheduled are "
        f"{', '.join(oth) if oth else 'none'}."
        + (f" A shared list pools the remaining demand from {', '.join(sh)}." if sh else ""))))
    add(dict(type="h2", text="2.3 Objectives"))
    add(dict(type="bullets", items=[
        f"Deliver about {n0(y3['cases'])} robotic operations a year by year 3.",
        f"Avoid about {n0(y3['open_avoided'])} open operations a year in patients who would otherwise have had open surgery.",
        f"Release about {n0(y3['bed_days'])} bed-days a year.",
        f"Keep booked robot utilisation at or above 85% (currently planned at {r['booked_utilisation']:.0%}).",
        "Report outcomes at 12 months against this case and to the NICE evidence generation plan."]))
    add(dict(type="pagebreak"))

    # 3 Economic case -----------------------------------------------------------------
    add(dict(type="h1", text="3. Economic case"))
    add(dict(type="h2", text="3.1 Method"))
    add(dict(type="p", text=(
        "The appraisal is a 30-day cost-consequence analysis. Costs are set alongside patient consequences "
        "(open operations avoided, bed-days, conversions, complications, returns to theatre and readmissions) "
        "without combining them into quality-adjusted life-years. Robust one-year quality-of-life data comparing "
        "robotic, laparoscopic and open surgery are not available for most procedures, so quality-adjusted "
        "life-years would have to be assumed rather than measured. Longer-term functional, oncological and hernia "
        "outcomes are not modelled.")))
    add(dict(type="p", text=(
        "For each specialty, the analysis asks what would have happened to the same patients without a robot "
        "(open or laparoscopic surgery, or robotic surgery at another centre in one sensitivity scenario) and "
        "applies the 30-day differences to that mix. The headline is the extra cost to the trust with no deduction "
        "for 30-day cost avoided. The economic view (section 3.7) deducts cost avoided and uses discounted cash at "
        "the HM Treasury Green Book rate of 3.5%, with capital in year 0 and residual value credited at year 5. "
        f"Activity above {pr.get('max_cases_per_robot', 700):,} robotic cases per robot per year is flagged as an "
        "advisory guardrail; it is not cut.")))
    add(dict(type="p", text=(
        "Activity comes from a two-week theatre template: each session's list type and its major, medium and "
        "minor cases are mapped to procedures (Appendix A), counted over the fortnight and extrapolated to a year. "
        "Where annual demand is entered, delivered cases are limited to demand and any shortfall is reported."
        if r["input_mode"] == "template" else
        "Activity comes from annual demand by specialty, planned into whole lists.")))
    add(dict(type="h2", text="3.2 Options appraised"))
    rows = [["Option 0: no robot", "n/a", "0", "0", "£0", "n/a", "£0"]]
    suggested = False
    for n in (1, 2):
        rn = run_with(base, robots=n)
        yn = rn["yearly"][min(3, H) - 1]
        star = ""
        if isinstance(base.get("template"), list) and n != cfg["robots"]:
            star, suggested = " *", True
        rows.append([f"Option {n}: {plural(n, 'robot')}{star}", f"{rn['booked_utilisation']:.0%}", n0(yn["cases"]),
                     n0(yn["bed_days"]), gbpm(rn["totals"]["extra_cost"]),
                     ratio(rn["totals"]["cost_per_bed_day_released"]), gbpm(rn["economic"]["net_present_cost"])])
    add(dict(type="table", header=["Option", "Utilisation", "Cases (yr 3)", "Bed-days (yr 3)",
                                   f"{H}-year extra cost", "Per bed-day released", "Net present cost"],
             widths=[1826, 1150, 1050, 1100, 1300, 1300, 1300], rows=rows, small=True))
    add(dict(type="p", text=(
        f"Preferred option: {robots_txt}. Option 0 avoids all programme costs but delivers none of the patient "
        "consequences above."
        + (" * This option uses a template suggested from demand, because the entered template is drawn for "
           f"{plural(cfg['robots'], 'robot')}." if suggested else ""))))
    add(dict(type="h2", text="3.3 Platform comparison"))
    if pf.get("procedure_set") == "single_port":
        add(dict(type="p", text=(
            "A single-port platform is appraised on its own eligible case mix (transoral, transanal, urological and "
            "thoracic procedures), with its own counterfactuals that include multi-port robotic surgery. It is "
            "therefore not compared line by line with multi-port platforms.")))
    else:
        prow = []
        for pk in ("platform_a", "platform_b", "platform_c"):
            rp = run_with(base, platform=pk)
            prow.append([D.PLATFORMS[pk]["label"], gbpm(rp["totals"]["extra_cost"]), ratio(rp["totals"]["cost_per_case"]),
                         gbpm(rp["economic"]["net_present_cost"]),
                         "Illustrative" if D.PLATFORMS[pk]["illustrative"] else "Published anchor"])
        add(dict(type="table", header=["Platform", f"{H}-year extra cost", "Per case", "Net present cost", "Price basis"],
                 widths=[3400, 1500, 1200, 1600, 1326], rows=prow))
    add(dict(type="h2", text="3.4 Comparison with a benchmark programme"))
    if bench is None:
        add(dict(type="p", text="The benchmark describes a multi-port programme and is not shown for a single-port platform."))
    else:
        add(dict(type="p", text=(
            "The benchmark describes a well-functioning multi-port programme run through the same model with the "
            "same clinical assumptions and unit costs, so the differences come from volume, case mix and price. "
            "Its case mix is renormalised from the three specialties (urology, general surgery and gynaecology) that "
            "made up 90% of UK NHS robotic procedures in 2024, so other specialties are excluded. Each benchmark "
            "value is sourced; values without a published source are labelled as assumptions.")))
        add(dict(type="table", header=["Measure", "This proposal", "Benchmark", "Benchmark source"],
                 widths=[2700, 1300, 1300, 3726], rows=[list(x) for x in BM.comparison_rows(r, bench)], small=True))
        add(dict(type="p", text=(
            f"The benchmark volume needs about {bench['booked_sessions_per_fortnight']:.1f} half-day "
            f"session-equivalents a fortnight at this tool's cases per list, against "
            f"{r['capacity_per_fortnight'] // cfg['robots']} per robot assumed here. High-volume programmes reach "
            "it with longer operating days, for example three-session days (GIRFT 2025).")))
    add(dict(type="h2", text="3.5 Sensitivity analysis"))
    add(dict(type="p", text=(
        "Each assumption is moved on its own to a low and a high value while everything else, including the list "
        "plan, stays at the base case. Bars are ordered by how much they move the result. Ranges are placeholders "
        "for expert review. The first chart shows the five-year extra cost, which clinical assumptions barely "
        "affect; the second shows the extra cost per bed-day released, which they drive.")))
    tor_cost = S.tornado(cfg, "extra_cost", r)
    tor_bed = S.tornado(cfg, "cost_per_bed_day", r) if t["bed_days"] > 0 else None
    if include_charts:
        add(dict(type="image", data=charts.tornado_png(tor_cost), width_cm=16,
                 caption=f"Figure 1. One-way sensitivity: {tor_cost['metric_label'].lower()}."))
        if tor_bed is not None:
            add(dict(type="image", data=charts.tornado_png(tor_bed), width_cm=16,
                     caption=f"Figure 2. One-way sensitivity: {tor_bed['metric_label'].lower()}."))
    trow = [[b["name"], b["low_label"], b["high_label"], gbp(b["low"]), gbp(b["high"])] for b in tor_cost["bars"]]
    add(dict(type="table", header=["Assumption", "Low", "High", "Extra cost at low", "Extra cost at high"],
             widths=[3300, 1300, 1300, 1563, 1563], rows=trow, small=True))
    if tor_bed is not None:
        trow = [[b["name"], b["low_label"], b["high_label"], gbp(b["low"]), gbp(b["high"])] for b in tor_bed["bars"]]
        add(dict(type="table", header=["Assumption", "Low", "High", "Per bed-day at low", "Per bed-day at high"],
                 widths=[3300, 1300, 1300, 1563, 1563], rows=trow, small=True))
    add(dict(type="h3", text="Scenarios"))
    ip = cfg["instrument_price_setting"]
    scen = [("Base case (as configured)", {}),
            ("No 30-day benefit", dict(evidence="no_benefit")),
            ("All benefits halved", dict(evidence="conservative")),
            ("All benefits 1.5 times", dict(evidence="optimistic"))]
    g_pro = cfg["groups"].get("prostatectomy")
    if g_pro is not None and g_pro["volume"] > 0 and not E.is_multi_comparator(g_pro) \
            and g_pro.get("p_robot_elsewhere", 0) < 1:
        scen.append(("Prostatectomy: robotic surgery at another centre instead of open",
                     dict(group_overrides=PROSTATE_ELSEWHERE)))
    for key in ("list", "standard_discount", "volume_discount"):
        if key != ip and pf.get("instruments_per_case") and not pf.get("instruments_included"):
            scen.append(("Instruments: " + D.INSTRUMENT_PRICE_LABELS[key].lower(), dict(instrument_price=key)))
    for v in D.CENTRAL_CAPITAL_OPTIONS:
        if v != inj and pf["model"] == "purchase":
            scen.append((f"Central capital {gbp(v)} per robot" if v else "No central capital (trust funds all capital)",
                         dict(central_capital_per_robot=v)))
    srow = []
    for lbl, kw in scen:
        rs = run_with(base, **kw)
        srow.append([lbl, gbpm(rs["totals"]["extra_cost"]), ratio(rs["totals"]["cost_per_bed_day_released"]),
                     ratio(rs["totals"]["cost_per_open_operation_avoided"]), gbpm(rs["economic"]["net_present_cost"])])
    add(dict(type="table", header=["Scenario", f"{H}-year extra cost", "Per bed-day released",
                                   "Per open operation avoided", "Net present cost"],
             widths=[3226, 1450, 1450, 1450, 1450], rows=srow, small=True))
    add(dict(type="h2", text="3.6 Break-even"))
    be = r["break_even"]
    add(dict(type="p", text=break_even_sentence(be) + (
        " The search is limited to the volume the programme could actually deliver: every available session filled "
        "at the planned cases per session.")))
    if be.get("max_cases"):
        add(dict(type="table", header=["Measure (steady state, per year)", "Value"], widths=[6500, 2526], rows=[
            ["Planned robotic cases", n0(be["planned_cases"])],
            ["Maximum deliverable cases", n0(be["max_cases"])],
            ["Extra cost less 30-day cost avoided at the planned volume", gbp(be["net_cost_at_plan"])],
            ["Extra cost less 30-day cost avoided at the maximum volume", gbp(be["net_cost_at_max"])],
            ["Break-even volume", n0(be["break_even_cases"]) if be["break_even_cases"] else "not reached"]]))
    add(dict(type="h2", text="3.7 Economic view (net of 30-day cost avoided)"))
    add(dict(type="table", header=["Measure", "Value"], widths=[6500, 2526], rows=[
        [f"Net present cost to the NHS ({H} years, 3.5%)", gbpm(r["economic"]["net_present_cost"])],
        ["30-day cost avoided over five years", gbp(t["offsets"])],
        ["Net cost per robotic operation", ratio(t["net_cost_per_case"])],
        ["Net cost per open operation avoided", ratio(t["net_cost_per_open_operation_avoided"])],
        ["Net cost per bed-day released", ratio(t["net_cost_per_bed_day_released"])]]))
    add(dict(type="p", text=(
        "The net present cost counts capital in full in year 0 whoever pays it, so it does not change with central "
        "capital. 30-day cost avoided is an economic value: it becomes cash only if beds or staff are removed or the "
        "released capacity is used for income-earning activity.")))
    add(dict(type="h2", text="3.8 Benefits not valued in cash"))
    add(dict(type="bullets", items=[
        "Wider access to minimal access surgery for patients who would otherwise have open surgery.",
        "Surgical training and recruitment and retention of surgeons and theatre teams.",
        "Ergonomic benefit to surgeons.",
        "Capacity released by shorter stays, available for further elective activity."]))
    add(dict(type="pagebreak"))

    # 4 Commercial case --------------------------------------------------------------
    add(dict(type="h1", text="4. Commercial case"))
    add(dict(type="h2", text="4.1 Procurement route"))
    add(dict(type="p", text=(
        "[State the procurement route, for example the national framework for robotic medical equipment managed "
        "by NHS Supply Chain, or a competitive tender, and the evaluation criteria.] Four payment models have been "
        "compared on identical terms: outright purchase, lease, managed service and per-procedure fee.")))
    add(dict(type="h2", text="4.2 Price inputs used"))
    prow = [["Platform", pf["label"]], ["Procurement model", D.MODEL_LABELS[pf["model"]]]]
    basis = D.CONTRACT_BASIS_LABELS[pf.get("contract_volume_basis", "per_robot")]
    if pf["model"] == "purchase":
        prow += [["Capital per robot", gbp(pf["capital"])], ["Trade-in credit", gbp(pf.get("trade_in", 0))],
                 ["Central capital per robot", gbp(inj)], ["Asset life", f"{pf['asset_life_years']} years"],
                 ["Maintenance per robot per year", gbp(pf["maintenance_per_year"])]]
    elif pf["model"] == "managed_service":
        prow += [["Annual fee per robot", gbp(pf["annual_fee"])],
                 [f"Cases included ({basis})", n0(pf["cases_included"])],
                 ["Excess fee per case", gbp(pf["excess_fee_per_case"])]]
    elif pf["model"] == "lease":
        prow += [["Lease per robot per year", gbp(pf["lease_per_year"])]]
    else:
        prow += [["Fee per case", gbp(pf["fee_per_case"])],
                 [f"Minimum cases per year ({basis})", n0(pf["minimum_cases_per_year"])]]
    if pf.get("instruments_included") or pf["model"] == "per_procedure":
        prow += [["Instrument price per case", "Included in the fee"]]
    else:
        prow += [["Instrument price per case",
                  f"{gbp(pf['instruments_per_case'])} ({D.INSTRUMENT_PRICE_LABELS[cfg['instrument_price_setting']].lower()})"]]
    prow += [["Price basis", pf["source"]]]
    add(dict(type="table", header=["Item", "Value"], widths=[3600, 5426], rows=prow))
    if pf["model"] in ("managed_service", "per_procedure"):
        add(dict(type="p", text=(
            f"Contract volumes are applied {basis}. [Confirm with the supplier whether included or minimum volumes "
            "apply to each robot or to the contract as a whole.]")))
    add(dict(type="h2", text="4.3 Negotiating targets"))
    pt = r["price_targets"]
    if pt["applicable"]:
        add(dict(type="table", header=["Target (net of 30-day cost avoided)", "Instrument price per case needed"],
                 widths=[5600, 3426], rows=[
                     ["Current assumption", gbp(pt["current_price"])],
                     ["Supplier list price", gbp(pt["list_price"])],
                     [f"Net cost of {gbp(pt['target_net_cost_per_bed_day'])} per bed-day released", gbp(pt["price_for_target"])],
                     ["Budget neutral at 30 days", gbp(pt["budget_neutral_price"])]]))
        add(dict(type="p", text=(
            "Prices are calculated at the planned steady-state volume and count 30-day cost avoided. "
            "'Not achievable' means the target cannot be met even at zero instrument cost.")))
    else:
        add(dict(type="p", text=pt["note"]))
    add(dict(type="h2", text="4.4 Contract protections sought"))
    add(dict(type="bullets", items=[
        "Instrument price fixed or capped for the contract term.",
        "Uptime guarantee with service credits.",
        "Training and proctoring included for an agreed number of surgeons and theatre staff.",
        "Upgrade, replacement and trade-in terms defined in advance.",
        "Contract volumes stated clearly as per robot or per contract.",
        "Data access for the 12-month review and NICE evidence generation."]))
    add(dict(type="pagebreak"))

    # 5 Financial case ------------------------------------------------------------------
    add(dict(type="h1", text="5. Financial case"))
    add(dict(type="p", text=(
        f"The table shows the extra income and expenditure cost to {trust} by year. Depreciation and public "
        "dividend capital apply to trust-funded capital only. Nothing is deducted for 30-day cost avoided, which "
        "is shown below the table for information.")))
    hdr = ["£ (thousands)"] + [f"Year {y['year']}" for y in r["yearly"]] + ["Total"]

    def line(lbl, f):
        vals = [f(y) for y in r["yearly"]]
        return [lbl] + [gbpk(v) for v in vals] + [gbpk(sum(vals))]

    rows = [line("Platform", lambda y: y["platform_fixed"])]
    if any(y["instruments"] for y in r["yearly"]):
        rows.append(line("Instruments", lambda y: y["instruments"]))
    rows += [line("Sterile services", lambda y: y["decontamination"]),
             line("Surgical first assistant", lambda y: y["staffing"]),
             line("Extra theatre time", lambda y: y["theatre_time_cost"]),
             line("Implementation and training", lambda y: y["implementation"]),
             line("Theatre works", lambda y: y["theatre_modification"]),
             line("Extra cost to the trust", lambda y: y["extra_cost"])]
    add(dict(type="table", header=hdr, widths=[2626] + [1067] * 5 + [1065], rows=rows, bold_last=True))
    if t["tariff_income"]:
        add(dict(type="table", header=["Cash case"] + hdr[1:], widths=[2626] + [1067] * 5 + [1065], rows=[
            line("Extra cost to the trust", lambda y: y["extra_cost"]),
            line("Less extra tariff income", lambda y: -y["tariff_income"]),
            line("Net cash cost to the trust", lambda y: y["net_cash_cost"])], bold_last=True))
    add(dict(type="p", text=TARIFF_NOTE))
    add(dict(type="table", header=["For information (not cash)"] + hdr[1:], widths=[2626] + [1067] * 5 + [1065], rows=[
        line("30-day cost avoided", lambda y: y["offsets"]),
        line("Extra cost less cost avoided", lambda y: y["net_cost"])], small=True))
    if include_charts:
        add(dict(type="image", data=charts.cost_offset_png(r["yearly"]), width_cm=16,
                 caption="Figure 3. Extra cost to the trust by year, with 30-day cost avoided shown for comparison."))
    add(dict(type="p", text=(
        f"Capital: {gbp(cap['total'])} in total, of which {gbp(cap['central'])} is assumed from central funds. "
        "[Confirm the capital source, the revenue budget holder, VAT treatment and the capital replacement plan.]")
        if pf["model"] == "purchase" else
        "No capital is required under this payment model. [Confirm the revenue budget holder.]"))
    add(dict(type="pagebreak"))

    # 6 Management case -----------------------------------------------------------------
    add(dict(type="h1", text="6. Management case"))
    if r["input_mode"] == "template":
        B.extend(template_blocks(r))
    else:
        B.extend(legacy_plan_blocks(r))
    add(dict(type="h2", text="6.2 Governance, workforce and training"))
    add(dict(type="bullets", items=[
        "[Name the robotic steering committee, its executive chair and reporting line.] The committee approves "
        "every new indication and owns delivery of this business case (GIRFT 2025).",
        "Each specialty names a clinical benefit owner and robotic lead, and agrees a credentialing and "
        "proctoring pathway.",
        f"A surgical first assistant or surgical care practitioner is funded at {pr.get('sfa_wte_per_robot', 0):g} "
        "whole-time equivalent per robot.",
        f"Learning curve allowed for: benefits are scaled to {pr['learning_benefit_by_year'][0]:.0%} in year 1 and "
        f"{pr['learning_benefit_by_year'][1]:.0%} in year 2.",
        f"Utilisation ramps from {pr['utilisation_by_year'][0]:.0%} in year 1 to {pr['utilisation_by_year'][1]:.0%} "
        f"in year 2 and {pr['utilisation_by_year'][2]:.0%} from year 3."]))
    add(dict(type="h2", text="6.3 Benefits realisation at 12 months"))
    add(dict(type="table", header=["Measure", "Planned (year 1)", "Actual", "Source"],
             widths=[3400, 1800, 1500, 2326], rows=[
                 ["Robotic operations", n0(r["yearly"][0]["cases"]), "", "Theatre system"],
                 ["Utilisation in year 1", f"{r['booked_utilisation'] * pr['utilisation_by_year'][0]:.0%}", "", "Theatre system"],
                 ["Open operations avoided", n0(r["yearly"][0]["open_avoided"]), "", "Local audit"],
                 ["Bed-days released", n0(r["yearly"][0]["bed_days"]), "", "Patient administration system"],
                 ["Conversions to open surgery", "Track rate", "", "Operation notes"],
                 ["Returns to theatre within 30 days", "Track rate", "", "Local audit"],
                 ["Readmissions within 30 days", "Track rate", "", "Patient administration system"],
                 ["Extra cost to the trust", gbp(r["yearly"][0]["extra_cost"]), "", "Finance"],
                 ["Instrument cost per case", gbp(pf.get("instruments_per_case", 0)), "", "Finance"]]))
    add(dict(type="h2", text="6.4 Key risks"))
    add(dict(type="table", header=["Risk", "Mitigation"], widths=[3800, 5226], rows=[
        ["Robot under-used", "Protected sessions in job plans; shared list for smaller specialties; quarterly utilisation review."],
        ["Too few trained surgeons to fill the lists", "Training plan by specialty agreed before go-live; proctoring funded."],
        ["Instrument prices rise", "Price cap in contract; review at renewal."],
        ["Benefits smaller than assumed", "Sensitivity analysis shown; specialty review of assumptions; 12-month review against plan."],
        ["Laparoscopic cases moved to the robot with little benefit", "Monitor the share of cases displacing open surgery."],
        ["Training delays", "Phased start by specialty; proctoring agreed in advance."]]))
    add(dict(type="pagebreak"))

    # Appendices ----------------------------------------------------------------------------
    add(dict(type="h1", text="Appendix A. Clinical assumptions by specialty"))
    add(dict(type="p", text=(
        "Reductions are robotic versus the comparator, at 30 days, per case. 'Share' is the proportion of these "
        "patients who would have had that comparator without the robot. All values are best-available estimates "
        "pending specialty review; any changes from the defaults are listed in Appendix C.")))
    arow = []
    for row in E.prior_rows(cfg):
        if not cfg["groups"][row["group"]]["volume"]:
            continue
        arow.append([row["specialty"], D.COMPARATOR_SHORT[row["comparator"]], f"{row['share']:.0%}",
                     f"{row['los']:g}", f"{row['conv']:.1%}", f"{row['comp']:.1%}", f"{row['reop']:.1%}",
                     f"{row['readm']:.1%}", f"{row['extra_minutes']:g}"])
    add(dict(type="table", header=["Specialty", "Without the robot", "Share", "Bed-days saved",
                                   "Conversions avoided", "Complications avoided", "Returns to theatre avoided",
                                   "Readmissions avoided", "Extra minutes"],
             widths=[2000, 1300, 650, 800, 850, 950, 900, 900, 676], rows=arow, small=True))
    add(dict(type="h3", text="Rationale and sources"))
    add(dict(type="table", header=["Specialty", "Counterfactual rationale", "Evidence"], widths=[2400, 3300, 3326],
             rows=[[g["label"], g["p_open_rationale"],
                    g.get("evidence_note") or D.EVIDENCE_NOTES.get(k, D.DEFAULT_EVIDENCE_NOTE)]
                   for k, g in cfg["groups"].items() if g["volume"]], small=True))
    add(dict(type="h3", text="How the theatre template maps to procedures"))
    add(dict(type="p", text=(
        "Each session on the template has a list type and a number of major, medium and minor cases. The table "
        "shows which procedure each tier counts as, and the split where a tier covers several procedures. "
        "'Not modelled' cases are costed but carry no 30-day benefit. Changes from the defaults are listed in "
        "Appendix C.")))
    mrows = []
    for lt, spec in cfg["list_map"].items():
        for tier in D.TIERS:
            if spec.get(tier):
                mrows.append([spec["label"], tier.capitalize(), T.describe_split(cfg, spec[tier])])
    mrows.append(["Any other list type or tier", "", "Not modelled"])
    add(dict(type="table", header=["List type", "Tier", "Counts as"], widths=[2600, 1200, 5226], rows=mrows,
             small=True))
    add(dict(type="h3", text="Tariff: extra income per robotic case (cash case only)"))
    add(dict(type="table", header=["Procedure", "Extra income per case", "Source"], widths=[3000, 1600, 4426],
             rows=[[g["label"], gbp(g.get("tariff_uplift", 0.0)),
                    D.TARIFF_SOURCES.get(k, D.DEFAULT_TARIFF_SOURCE)]
                   for k, g in cfg["groups"].items() if g["volume"] or g.get("tariff_uplift")], small=True))
    add(dict(type="h1", text="Appendix B. Unit costs and programme settings"))
    uc = cfg["unit_costs"]
    add(dict(type="table", header=["Input", "Value", "Note"], widths=[3400, 1600, 4026], rows=[
        ["Excess bed-day", gbp(uc["bed_day"]), D.EVIDENCE_NOTES["bed_day"]],
        ["Return to theatre (non-ward)", gbp(uc["reoperation"]), D.DEFAULT_EVIDENCE_NOTE],
        ["Major complication (non-ward)", gbp(uc["major_complication"]), D.DEFAULT_EVIDENCE_NOTE],
        ["Readmission (full spell)", gbp(uc["readmission"]), D.DEFAULT_EVIDENCE_NOTE],
        ["Conversion to open (non-ward)", gbp(uc["conversion"]), D.DEFAULT_EVIDENCE_NOTE],
        ["Extra theatre minute", gbp(uc["theatre_minute"]), "Costed by default, which is conservative. Placeholder."],
        ["Sterile services per robotic case", gbp(uc.get("decontamination_per_case", 0)), "Placeholder; replace with the local sterile services charge."],
        ["Surgical first assistant", f"{pr.get('sfa_wte_per_robot', 0):g} WTE per robot at {gbp(pr.get('sfa_cost_per_wte', 0))}",
         "National guidance says provision should be built into the business case (GIRFT 2025); cost is a placeholder. Use local pay rates."],
        ["Theatre works per robot (one-off)", gbp(pr.get("theatre_modification_per_robot", 0)), "Placeholder; confirm with estates."],
        ["Implementation, training and proctoring per robot", gbp(pr["implementation_cost_per_robot"]), "One-off, year 1. Placeholder."],
        ["Operating weeks per year", str(pr["operating_weeks_per_year"]), ""],
        ["Sessions per robot per week", str(pr["sessions_per_robot_per_week"]), "One slot kept for maintenance."],
        ["Cases per robot per year: advisory level", f"{pr.get('max_cases_per_robot', 700):,}",
         "Amber guardrail above this level; activity is not cut."],
        ["Minimum list fill", f"{pr.get('min_list_fill', 0.75):.0%}", "Lists below this fill are flagged."],
        ["Maximum cases per session", str(pr.get("max_cases_per_session", 3)), "Template entries above this are flagged."],
        ["Share of templated cases that go ahead", f"{pr.get('realisation_factor', 1.0):.0%}",
         "Allows for cancellations. Placeholder."],
        ["Discount rate", f"{pr['discount_rate']:.1%}", "HM Treasury Green Book."],
        ["Public dividend capital", f"{pr['pdc_rate']:.1%}", "On average net book value."]], small=True))
    add(dict(type="p", text=(
        "Length-of-stay reductions include stay caused by complications, so complication and return-to-theatre "
        "costs exclude ward days to avoid double counting.")))
    add(dict(type="h1", text="Appendix C. Model checks"))
    add(dict(type="p", text=(
        f"Engine version {cfg['version']}. The calculation engine is covered by an automated test suite including "
        "hand-calculated cases and an independent re-calculation of all cost avoided.")))
    if r["user_modified"]:
        add(dict(type="table", header=["Assumption changed", "Default", "Used"], widths=[5400, 1800, 1826],
                 rows=[[E.describe_item(cfg, m["item"]), E.fmt_value(m["default"]), E.fmt_value(m["used"])]
                       for m in r["user_modified"]], small=True))
    else:
        add(dict(type="p", text="No clinical assumptions or unit costs were changed from the defaults."))
    if r["warnings"]:
        add(dict(type="h3", text="Warnings raised by the tool"))
        add(dict(type="bullets", items=r["warnings"]))
    add(dict(type="h1", text="Appendix D. Assumptions register"))
    from collections import Counter
    cnt = Counter(x["status"] for x in reg)
    add(dict(type="p", text=(
        "Every input the case depends on, with its source, evidence grade, status and the person who must sign it "
        "off. " + "; ".join(f"{v} {k.lower()}" for k, v in sorted(cnt.items())) + ". No entry has yet been reviewed "
        "by the relevant specialty.")))
    add(dict(type="table", header=["Assumption", "Value", "Source", "Status", "Owner"],
             widths=[2500, 1100, 2926, 1100, 1400],
             rows=[[x["parameter"], x["value"], x["source"], x["status"], x["owner"]] for x in reg], small=True))
    add(dict(type="h1", text="Appendix E. References"))
    add(dict(type="numbered", items=REFERENCES))
    return B, r


REFERENCES = [
    "National Institute for Health and Care Excellence. Robot-assisted surgery for soft tissue procedures: early value assessment. HealthTech guidance 742 (HTE21). London: NICE, April 2025.",
    "NHS England, Getting It Right First Time. Implementation of robotic-assisted surgery (RAS) in England. London: NHS England, July 2025.",
    "Donald N, Sebastian J, Preziosi G. National adoption of robotic-assisted surgery in the United Kingdom: a decade of growth, distribution and speciality trends (2014-2024). Surg Endosc 2026; 40: 4358-67.",
    "HM Treasury. The Green Book: central government guidance on appraisal and evaluation. London: HM Treasury, 2022.",
    "HM Treasury. Guide to developing the project business case (Five Case Model). London: HM Treasury, 2018.",
    "Does the pre-conversion platform matter? A comparison of laparoscopic and robotic converted to open colectomies. Surg Endosc 2024. doi:10.1007/s00464-024-11079-0.",
    "Trastulli S, Cirocchi R, Desiderio J, et al. Robotic versus laparoscopic approach in colonic resections for cancer and benign diseases: systematic review and meta-analysis. PLoS One 2015; 10: e0134062.",
    "National Bowel Cancer Audit. State of the Nation report 2025. London: Healthcare Quality Improvement Partnership, 2025.",
    "Clark TJ, Saridogan E. Is there still need for a further randomised controlled trial on the route of hysterectomy for benign disease? Facts Views Vis Obgyn 2021; 13: 103-05.",
    "Robotic surgery in emergency general surgery: an overview of UK practice. World J Emerg Surg 2025. doi:10.1186/s13017-025-00658-8.",
    "UK Parliament. Hospital beds: costs. Written question UIN 100046, answered 22 December 2025.",
    "Kishore, Khairnar MR, Burton E, Sidana A, Saini S. Single-port vs. multi-port robotic radical prostatectomy: an umbrella review of meta-analyses. J Robot Surg 2026; 20: 821.",
    "Wallace BK, Dishong DM, Cohen AJ. Single-port robotic prostatectomy is associated with higher same-day discharge and reduced length of stay: a NSQIP analysis. World J Urol 2026 (published online Sept 10).",
    "Abaza R, Murphy C, Bsatee A, Brown DH Jr, Martinez O. Single-port robotic surgery allows same-day discharge in majority of cases. Urology 2021; 148: 159-65.",
    "Single port robotic urologic surgery: fewer ports, higher costs. American Urological Association Annual Meeting 2022 (abstract MP32-10).",
    "[Add local and national references as required.]",
]


def build_docx_bytes(case, include_charts=True):
    blocks, r = build_blocks(case, include_charts=include_charts)
    return docx_render.to_bytes(blocks), r


def main(case_path, out_path):
    case = json.loads(Path(case_path).read_text())
    data, _ = build_docx_bytes(case)
    Path(out_path).write_bytes(data)
    print(f"Written {out_path}")



TARIFF_NOTE = (
    "Tariff: the income line counts only the difference over what the trust would earn for the same patients "
    "without the robot, entered per procedure, and assumes those patients would otherwise be treated at this "
    "trust. It appears in the trust's cash case only. It is a transfer within the NHS, so it is excluded from the "
    "economic view (net present cost) and from the cost per outcome.")


def template_blocks(r):
    cfg = r["config"]
    pr = cfg["programme"]
    ts = r["template_summary"]
    out = [dict(type="h2", text="6.1 Two-week theatre template")]
    variant = {"standard": "pre-filled from demand, standard day", "extended": "pre-filled from demand, extended day",
               "custom": "entered by the trust"}.get(cfg.get("template_variant"), "entered by the trust")
    out.append(dict(type="p", text=(
        f"The template ({variant}) covers 14 days, Monday to Sunday twice, with AM, PM and evening sessions on each "
        f"robot. Standard hours are weekday AM and PM, with Friday PM kept for maintenance; evening and weekend "
        f"sessions count only when used. {ts['booked']} of {ts['available']} available sessions per fortnight are "
        f"booked ({r['booked_utilisation']:.0%}). The fortnight is extrapolated to {pr['operating_weeks_per_year']} "
        f"operating weeks a year, and {pr.get('realisation_factor', 1.0):.0%} of templated cases are assumed to go "
        "ahead.")))
    rows = []
    for k, g in r["groups"].items():
        if g.get("template_cases", 0) < 0.5 and g["unmet_cases"] < 0.5:
            continue
        rows.append([g["label"], f"{g['sessions_per_fortnight']:.1f}", n0(g.get("template_cases", 0)),
                     n0(g["ceiling"]) if cfg.get("demand_check", True) and k not in D.NOT_MODELLED else "not checked",
                     n0(g["planned_cases"]), n0(g["unmet_cases"])])
    out.append(dict(type="table", header=["Procedure", "Sessions per fortnight", "Cases on template (year)",
                                          "Demand (year)", "Cases delivered", "Unmet demand"],
                    widths=[3100, 1100, 1300, 1200, 1200, 1126], rows=rows, small=True))
    out.append(dict(type="p", text=(f"Total unmet demand: {n0(r['unmet_cases'])} cases a year."
                                    if r["unmet_cases"] >= 0.5 else "All demand entered is scheduled.")))
    for rb in range(1, cfg["robots"] + 1):
        grid_rows = []
        for w in (1, 2):
            for d in D.DAYS:
                row = [f"Week {w} {d}"]
                for sname in D.SESSIONS:
                    cell = next(x for x in ts["cells"] if x["robot"] == rb and x["week"] == w
                                and x["day"] == d and x["session"] == sname)
                    row.append(cell_text(cfg, cell))
                if d in ("Sat", "Sun") and all(x == "" for x in row[1:]):
                    continue
                grid_rows.append(row)
        out.append(dict(type="h3", text=f"Robot {rb}: two-week template"))
        out.append(dict(type="table", header=["", "AM", "PM", "Evening"], widths=[1526, 2500, 2500, 2500],
                        rows=grid_rows, small=True))
    out.append(dict(type="p", text="Saturdays and Sundays are shown only where a session is in use."))
    return out


def cell_text(cfg, cell):
    if cell["status"] == "booked":
        lt = T.label_of(cfg, cell["list_type"]) if cell["list_type"] else ""
        return f"{lt}: {cell['entry'].lower() if cell['entry'] == 'Continuing' else cell['entry']}".strip(": ")
    if cell["status"] == "open":
        return "Unbooked"
    if cell["status"] in ("closed", "maintenance"):
        return cell["status"].capitalize()
    return ""


def legacy_plan_blocks(r):
    cfg = r["config"]
    pr = cfg["programme"]
    thr = pr.get("min_list_fill", 0.75)
    out = [dict(type="h2", text="6.1 Fortnightly list plan")]
    out.append(dict(type="p", text=(
        f"Capacity is {r['capacity_per_fortnight']} sessions per fortnight ({pr['sessions_per_robot_per_week']} per "
        f"robot per week, one weekly slot kept for maintenance); {r['booked_sessions_per_fortnight']:g} are booked "
        f"and {r['spare_sessions_per_fortnight']:g} left free. A dedicated list is created only if it would be at "
        f"least {thr:.0%} full; smaller remaining demand is pooled on a shared list, again only if that list would "
        f"be at least {thr:.0%} full.")))
    prow = []
    for k, v in r["plan"].items():
        if k == E.SHARED or not (v or r["groups"][k]["shared_cases"] >= 0.5):
            continue
        g = cfg["groups"][k]
        go = r["groups"][k]
        prow.append([g["label"], str(v), f"{g['cases_per_list']:g} per {'all-day' if g['list_sessions'] == 2 else 'half-day'} list",
                     n0(go["dedicated_cases"]), n0(go["shared_cases"]), n0(go["unmet_cases"])])
    if r["plan"].get(E.SHARED):
        fill = r["shared"]["shared_fill"]
        prow.append([E.shared_label(), str(r["plan"][E.SHARED]), f"half-day, {fill:.0%} full", "",
                     n0(sum(g["shared_cases"] for g in r["groups"].values())), ""])
    out.append(dict(type="table", header=["Specialty", "Sessions per fortnight", "List", "Cases on own lists",
                                          "Cases on shared list", "Unmet demand"],
                    widths=[3000, 1200, 1700, 1100, 1100, 926], rows=prow))
    out.append(dict(type="p", text=(f"Total unmet demand: {n0(r['unmet_cases'])} cases a year."
                                    if r["unmet_cases"] >= 0.5 else "All demand entered is scheduled.")))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    for rb in range(1, cfg["robots"] + 1):
        grid_rows = []
        for w in (1, 2):
            for sname in ("AM", "PM"):
                row = [f"Week {w} {sname}"]
                for d in days:
                    cell = next((x for x in r["grid"] if x["robot"] == rb and x["week"] == w
                                 and x["day"] == d and x["session"] == sname), None)
                    row.append("Maintenance" if cell is None else
                               (E.slot_label(cfg, cell["group"]) if cell["group"] else "Unbooked"))
                grid_rows.append(row)
        out.append(dict(type="h3", text=f"Robot {rb}: two-week rota"))
        out.append(dict(type="table", header=[""] + days, widths=[1426] + [1520] * 5, rows=grid_rows, small=True))
    return out


if __name__ == "__main__":
    main(*sys.argv[1:3])
