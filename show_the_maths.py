"""
Produce a step-by-step worked example ("show the maths") for any preset.
Usage: python3 show_the_maths.py [preset] [platform] [evidence] > worked_example.md
"""
import sys

import business_case as BC
import defaults as D
import engine as E
import templates as T


def gbp(x):
    return "n/a" if x is None else f"£{x:,.0f}"


def main(preset="medium_dgh_1", platform="platform_b", evidence="central", template="standard"):
    cfg = E.build_config(preset, platform, evidence, template=template)
    r = E.run(cfg)
    pr, uc, pf = cfg["programme"], cfg["unit_costs"], cfg["platform"]
    f = E.fortnights_per_year(cfg)
    out = []
    w = out.append
    w(f"# Worked example: {cfg['preset_label']}, {pf['label']}, {evidence} evidence")
    w(f"Engine version {cfg['version']}. All inputs are placeholders for expert review.\n")

    if r["input_mode"] == "template":
        ts = r["template_summary"]
        w("## Step 1 to 3. Two-week theatre template")
        w(f"Template: {cfg.get('template_variant')}. Each robot has 14 days x 3 sessions (AM session 1, PM session 2, "
          "PM session 3), one procedure per session. Standard hours are weekday sessions 1 and 2 (Friday session 2 "
          "maintenance); session 3 and weekend sessions count only when used. Cases per session follow complexity: "
          "High 1, Medium 1.5, Low 3, whole day 0.5.")
        w(f"Booked sessions per fortnight = {ts['booked']}; available = {ts['available']}; utilisation = "
          f"{ts['booked']} / {ts['available']} = {r['booked_utilisation']:.0%}.")
        w(f"Annual cases = cases per fortnight x {f:g} fortnights x {pr.get('realisation_factor', 1.0):.0%} going "
          f"ahead; then limited to demand (check {'on' if cfg.get('demand_check', True) else 'off'}). Above "
          f"{pr['max_cases_per_robot']:,} per robot a year is flagged amber (advisory), not cut.\n")
        w("| Procedure | Cases per fortnight | On template (year) | Demand | Delivered | Unmet |")
        w("| --- | --- | --- | --- | --- | --- |")
        for k, g in cfg["groups"].items():
            go = r["groups"][k]
            if ts["cases_per_fortnight"][k] < 1e-9 and go["unmet_cases"] < 0.5:
                continue
            w(f"| {g['label']} | {ts['cases_per_fortnight'][k]:.2f} | {go['template_cases']:.0f} | {go['ceiling']:.0f} | "
              f"{go['planned_cases']:.0f} | {go['unmet_cases']:.0f} |")
        w("\nCases per booked session by procedure: " + "; ".join(
            f"{g['label'].split(' (')[0]} {g['cases_per_session']:g}" + (" (whole day)" if g.get("whole_day") else "")
            for g in cfg["groups"].values()) + ".\n")
    else:
        w("## Step 1 to 3. Demand, capacity and plan (v0.5 demand-led planner)")
        w(f"Capacity per fortnight = robots x sessions per week x 2 = {cfg['robots']} x "
          f"{pr['sessions_per_robot_per_week']} x 2 = {r['capacity_per_fortnight']}.")
        w(f"Fortnights per year = {pr['operating_weeks_per_year']} / 2 = {f:g}.")
        w(f"A dedicated list is created only if it would be at least {pr['min_list_fill']:.0%} full; leftover demand is "
          f"pooled on shared half-day sessions, again only if they would be at least {pr['min_list_fill']:.0%} full. "
          f"Above {pr['max_cases_per_robot']:,} cases per robot per year is flagged amber (advisory), not cut.\n")
        w("| Group | Robotic cases available | Open without robot | Cases per list | List | Sessions/fortnight | Own lists | Shared list | Unmet |")
        w("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for k, g in cfg["groups"].items():
            go = r["groups"][k]
            if g["volume"] == 0 and go["sessions_per_fortnight"] == 0:
                continue
            w(f"| {g['label']} | {g['volume']:g} | {(g['comparators'].get('open', 0) if 'comparators' in g else g['p_open']):.0%} | "
              f"{g['cases_per_list']:g} | {'all-day' if g['list_sessions'] == 2 else 'half-day'} | {go['sessions_per_fortnight']} | "
              f"{go['dedicated_cases']:.0f} | {go['shared_cases']:.0f} | {go['unmet_cases']:.0f} |")
        sh = r["shared"]
        if sh["shared_sessions"]:
            w(f"\nShared list: {sh['shared_sessions']} half-day sessions per fortnight, {sh['shared_fill']:.0%} full.")
        w(f"\nOwn-list cases = min(sessions x {f:g} x cases per list / sessions per list, cases available). "
          f"Booked {r['booked_sessions_per_fortnight']:g} of {r['capacity_per_fortnight']} sessions "
          f"({r['booked_utilisation']:.0%}). Robots needed to meet full demand: "
          f"{r['robots_needed']['fractional']:.2f}.\n")

    t = 3
    y = r["yearly"][t - 1]
    w(f"## Step 4 to 6. Patient consequences, year {t} (utilisation {y['utilisation']:.0%}, "
      f"benefit multiplier {y['benefit_multiplier']:.2f})")
    k = max(cfg["groups"], key=lambda x: r["groups"][x]["planned_cases"])
    g = cfg["groups"][k]
    ev = y["by_group"][k]
    m = y["benefit_multiplier"]
    w(f"Worked for one group ({g['label']}):\n")
    w(f"- Robotic cases = {r['groups'][k]['planned_cases']:.1f} x {y['utilisation']:.2f} = {ev['cases']:.1f}")
    for row in E.prior_rows(cfg):
        if row["group"] != k:
            continue
        n = ev["cases"] * row["share"]
        w(f"- Without the robot, {row['share']:.0%} would have {E.D.COMPARATOR_LABELS[row['comparator']].lower()} = {n:.1f} cases; "
          f"bed-days saved = {m:.2f} x {n:.1f} x {row['los']:g} = {m * n * row['los']:.1f}; "
          f"conversions avoided = {m * n * row['conv']:.2f}; complications avoided = {m * n * row['comp']:.2f}; "
          f"returns to theatre avoided = {m * n * row['reop']:.2f}")
    w(f"- Group totals: bed-days {ev['bed_days']:.1f}, complications {ev['complications']:.2f}, "
      f"returns to theatre {ev['reoperations']:.2f}, readmissions {ev['readmissions']:.2f}\n")
    w("All groups combined:\n")
    w("| Consequence | Year 3 |")
    w("| --- | --- |")
    for lbl, key in [("Robotic cases", "cases"), ("Open operations avoided", "open_avoided"),
                     ("Bed-days released", "bed_days"), ("Conversions avoided", "conversions"),
                     ("Reoperations avoided", "reoperations"),
                     ("Major complications avoided", "complications"),
                     ("Readmissions avoided", "readmissions"),
                     ("Extra elective cases enabled", "extra_elective_cases_enabled")]:
        w(f"| {lbl} | {y[key]:.1f} |")

    w(f"\n## Step 7 to 9. Extra cost and cost avoided, year {t}")
    for kk, v in y["platform_detail"].items():
        lab = {"pdc": "public dividend capital"}.get(kk, kk.replace("_", " "))
        w(f"- Platform {lab}: {gbp(v)}")
    w(f"- Instruments = {y['cases']:.1f} x {gbp(pf.get('instruments_per_case', 0))} = {gbp(y['instruments'])}")
    w(f"- Sterile services = {y['cases']:.1f} x {gbp(uc['decontamination_per_case'])} = {gbp(y['decontamination'])}")
    w(f"- Surgical first assistant = {cfg['robots']} x {pr['sfa_wte_per_robot']:g} WTE x {gbp(pr['sfa_cost_per_wte'])} = {gbp(y['staffing'])}")
    w(f"- Extra theatre time = {y['extra_minutes']:.0f} min x {gbp(uc['theatre_minute'])} = {gbp(y['theatre_time_cost'])}")
    w(f"- Extra cost to the trust = {gbp(y['extra_cost'])} ({gbp(y['extra_cost_per_case'])} per case). "
      "Nothing is deducted for 30-day cost avoided.")
    w(f"- 30-day cost avoided (economic view, not cash) = bed-days x {gbp(uc['bed_day'])} + conversions x {gbp(uc['conversion'])} + "
      f"reoperations x {gbp(uc['reoperation'])} + complications x {gbp(uc['major_complication'])} + "
      f"readmissions x {gbp(uc['readmission'])} = {gbp(y['offsets'])}")
    w(f"- Extra cost less cost avoided = {gbp(y['net_cost'])}")
    w(f"- Extra tariff income (cash case only) = {gbp(y['tariff_income'])}; net cash cost = {gbp(y['net_cash_cost'])}\n")

    w("## Five-year view")
    w("| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |")
    w("| --- | --- | --- | --- | --- | --- |")
    for yy in r["yearly"]:
        w(f"| {yy['year']} | {yy['cases']:.0f} | {yy['bed_days']:.0f} | {gbp(yy['extra_cost'])} | "
          f"{gbp(yy['offsets'])} | {gbp(yy['net_cost'])} |")
    tt = r["totals"]
    w(f"| Total | {tt['cases']:.0f} | {tt['bed_days']:.0f} | {gbp(tt['extra_cost'])} | "
      f"{gbp(tt['offsets'])} | {gbp(tt['net_cost'])} |\n")
    w(f"Economic case (discounted at {pr['discount_rate']:.1%}, capital in year 0, residual value "
      f"credited in year {pr['horizon_years']}): net present cost {gbp(r['economic']['net_present_cost'])}.\n")
    w("Cost per outcome (five-year extra cost divided by each consequence; not additive):\n")
    for lbl, key in [("per robotic case", "cost_per_case"),
                     ("per open operation avoided", "cost_per_open_operation_avoided"),
                     ("per bed-day released", "cost_per_bed_day_released"),
                     ("per serious event avoided", "cost_per_serious_event_avoided")]:
        w(f"- Extra cost {lbl}: {gbp(tt[key])}")
    w(f"\n{BC.break_even_sentence(r['break_even'])}")
    if r["warnings"]:
        w("\n## Guardrail warnings")
        for x in r["warnings"]:
            w(f"- {x}")
    if r["user_modified"]:
        w("\n## User-modified priors")
        for x in r["user_modified"]:
            w(f"- {E.describe_item(cfg, x['item'])}: default {x['default']:g}, used {x['used']:g}")
    print("\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
