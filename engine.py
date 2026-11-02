"""
Robotic programme decision engine: 30-day cost-consequence analysis (v0.8).

Pipeline (each step is a small, separately testable function):
  1. rota                two-week rota per robot: sessions available per day (0, 2 or 3) and,
                         per session, a procedure and its cases (1-4 or "cont.")
  2. cases               cases per fortnight x operating fortnights x share that go ahead,
                         then x utilisation ramp in year t. Above max_cases_per_robot x robots
                         is flagged amber (advisory), not cut
  3. counterfactual      open_g = cases x p_open ; elsewhere_g = cases x p_robot_elsewhere ;
                         lap_g = the rest (what would happen WITHOUT the robot)
  4. 30-day consequences events avoided = displaced cases x reduction x evidence x learning_t
  5. extra cost          platform + instruments + sterile services + surgical first assistant
                         + extra theatre time + one-off implementation and theatre works
                         (the headline: no deduction for bed-days or other 30-day offsets)
  6. cost avoided        events avoided x unit costs (economic view only; not cash)
  7. net of cost avoided 5 - 6, by year (financial) and discounted (economic)
  8. break-even          volume at which 5 - 6 = 0 at steady state, searched only up to every
                         available session booked at the rota's case mix

The hospital type only selects the starting example rota; no calculation depends on it.
No QALYs and no ICERs are computed, by design.
"""
from __future__ import annotations

import copy

import defaults as D
import templates as T

EVENT_KEYS = ["bed_days", "conversions", "reoperations", "complications", "readmissions"]
SHARED = "_shared"   # kept for saved cases from earlier versions; unused


# ---------------------------------------------------------------------------
# 0. Configuration
# ---------------------------------------------------------------------------
def build_config(preset="medium_dgh_1", platform="platform_b", evidence="central",
                 overrides=None, instrument_price="list", template="example"):
    """Assemble a full input set from defaults, then apply user overrides.

    overrides = {"groups": {gkey: {field: value}}, "unit_costs": {...},
                 "programme": {...}, "platform": {...}, "robots": int,
                 "existing_robots": "0".."5 or more"}
    template  = "example" (the hospital type's example rota), a rota grid (list per
                robot), or None (an empty rota).
    """
    p = D.PRESETS[preset]
    cfg = dict(
        preset=preset, preset_label=p["label"], hospital=p["hospital"], robots=p["robots"],
        evidence=evidence, evidence_multiplier=D.EVIDENCE_SETTINGS[evidence],
        groups=copy.deepcopy(D.PROCEDURE_GROUPS), unit_costs=copy.deepcopy(D.UNIT_COSTS),
        programme=copy.deepcopy(D.PROGRAMME),
        platform_key=platform, platform=copy.deepcopy(D.PLATFORMS[platform]), version=D.ENGINE_VERSION,
    )
    o = overrides or {}
    for gk, fields in o.get("groups", {}).items():
        if gk in cfg["groups"]:
            cfg["groups"][gk].update(copy.deepcopy(fields))
    cfg["unit_costs"].update(o.get("unit_costs", {}))
    cfg["programme"].update(o.get("programme", {}))
    cfg["platform"].update(o.get("platform", {}))
    if "robots" in o:
        cfg["robots"] = int(o["robots"])
    cfg["existing_robots"] = str(o.get("existing_robots", "0"))
    pf = cfg["platform"]
    pf["instruments_list_price"] = pf.get("instruments_per_case", 0)
    if isinstance(instrument_price, (int, float)):
        pf["instruments_per_case"] = float(instrument_price)
        cfg["instrument_price_setting"] = "custom"
    else:
        pf["instruments_per_case"] = pf["instruments_list_price"] * D.INSTRUMENT_PRICE_SETTINGS[instrument_price]
        cfg["instrument_price_setting"] = instrument_price
    if template == "example":
        cfg["template"] = T.example_rota(cfg["hospital"], cfg["robots"])
        cfg["template_variant"] = "example"
    elif template is None:
        cfg["template"] = T.empty_grid(cfg["robots"])
        cfg["template_variant"] = "empty"
    else:
        cfg["template"] = T.resize(template, cfg["robots"])
        cfg["template_variant"] = "custom"
    validate(cfg)
    return cfg


def validate(cfg):
    for gk, g in cfg["groups"].items():
        pe = g.get("p_robot_elsewhere", 0.0)
        if not 0 <= g["p_open"] <= 1 or not 0 <= pe <= 1 or g["p_open"] + pe > 1 + 1e-9:
            raise ValueError(f"{g['label']}: the open and robot-elsewhere shares must each lie between "
                             "0 and 1 and together not exceed 1")
        for k in D.BENEFIT_KEYS:
            if g[k] < 0:
                raise ValueError(f"{g['label']}: 30-day reductions are entered as positive numbers")
        if g.get("complexity") not in D.COMPLEXITY_LEVELS:
            raise ValueError(f"{g['label']}: complexity must be High, Medium or Low")
    pr = cfg["programme"]
    if len(pr["utilisation_by_year"]) < pr["horizon_years"]:
        raise ValueError("utilisation_by_year shorter than horizon")
    if len(pr["learning_benefit_by_year"]) < pr["horizon_years"]:
        raise ValueError("learning_benefit_by_year shorter than horizon")
    if cfg["robots"] < 1:
        raise ValueError("robots must be >= 1")
    if not 0 < pr.get("realisation_factor", 1.0) <= 1:
        raise ValueError("the share of rota cases that go ahead must lie between 0 and 100%")
    for k, v in cfg["unit_costs"].items():
        if v < 0:
            raise ValueError(f"{D.UNIT_COST_LABELS.get(k, k)}: unit costs cannot be negative")
    basis = cfg["platform"].get("contract_volume_basis", "per_robot")
    if basis not in ("per_robot", "per_contract"):
        raise ValueError("contract_volume_basis must be 'per_robot' or 'per_contract'")
    if cfg.get("existing_robots", "0") not in D.EXISTING_ROBOT_OPTIONS:
        raise ValueError("existing robots must be 0, 1, 2, 3, 4 or 5 or more")


MODIFIABLE = D.BENEFIT_KEYS + ["p_open", "p_robot_elsewhere", "complexity", "extra_minutes_open",
                               "extra_minutes_lap", "tariff_uplift"]


def modified_priors(cfg):
    """Every assumption or unit cost that differs from the defaults."""
    out = []
    for gk, g in cfg["groups"].items():
        ref = D.PROCEDURE_GROUPS[gk]
        for k in dict.fromkeys(MODIFIABLE):
            if g.get(k, 0.0) != ref.get(k, 0.0):
                out.append(dict(item=f"{gk}.{k}", default=ref.get(k, 0.0), used=g.get(k, 0.0)))
    for k, v in cfg["unit_costs"].items():
        if v != D.UNIT_COSTS[k]:
            out.append(dict(item=f"unit_costs.{k}", default=D.UNIT_COSTS[k], used=v))
    for k in ("sfa_cost_per_wte", "sfa_wte_per_robot"):
        if cfg["programme"].get(k) != D.PROGRAMME[k]:
            out.append(dict(item=f"programme.{k}", default=D.PROGRAMME[k], used=cfg["programme"].get(k)))
    return out


def fortnights_per_year(cfg):
    return cfg["programme"]["operating_weeks_per_year"] / 2


# ---------------------------------------------------------------------------
# 3-4. Counterfactual and 30-day patient consequences
# ---------------------------------------------------------------------------
def consequences(g, cases, multiplier):
    """Events avoided for a given number of robotic cases. multiplier =
    evidence setting x learning-curve factor for the year."""
    m = multiplier
    n_open = cases * g["p_open"]
    n_else = cases * g.get("p_robot_elsewhere", 0.0)
    n_lap = cases - n_open - n_else
    return dict(
        cases=cases, open_avoided=n_open, lap_displaced=n_lap, robot_elsewhere=n_else,
        bed_days=m * (n_open * g["los_reduction_open"] + n_lap * g["los_reduction_lap"]),
        conversions=m * n_lap * g["conv_reduction_lap"],
        reoperations=m * (n_open * g["reop_reduction_open"] + n_lap * g["reop_reduction_lap"]),
        complications=m * (n_open * g["comp_reduction_open"] + n_lap * g["comp_reduction_lap"]),
        readmissions=m * (n_open * g["readm_reduction_open"] + n_lap * g["readm_reduction_lap"]),
        extra_minutes=n_open * g["extra_minutes_open"] + n_lap * g["extra_minutes_lap"],
    )


def offsets_value(ev, uc):
    return (ev["bed_days"] * uc["bed_day"] + ev["conversions"] * uc["conversion"]
            + ev["reoperations"] * uc["reoperation"]
            + ev["complications"] * uc["major_complication"]
            + ev["readmissions"] * uc["readmission"])


# ---------------------------------------------------------------------------
# 5. Costs
# ---------------------------------------------------------------------------
def trust_capital(cfg):
    """Capital per robot carried by the trust after trade-in and any central injection."""
    pf = cfg["platform"]
    net = pf["capital"] - pf.get("trade_in", 0)
    return max(net - cfg["programme"].get("central_capital_per_robot", 0), 0.0)


def contract_multiplier(cfg):
    """Contract volumes apply per robot (x robots) or once per contract."""
    return cfg["robots"] if cfg["platform"].get("contract_volume_basis", "per_robot") == "per_robot" else 1


def platform_cost_year(cfg, t, total_cases):
    """Financial (income and expenditure) platform cost in year t (1-based),
    for the whole programme. Returns fixed and variable parts separately."""
    pf, pr, R = cfg["platform"], cfg["programme"], cfg["robots"]
    instruments = pf.get("instruments_per_case", 0) * total_cases
    m = pf["model"]
    if m == "purchase":
        net_cap = trust_capital(cfg)
        dep = net_cap / pf["asset_life_years"]
        nbv_start = max(net_cap - dep * (t - 1), 0)
        dep_t = min(dep, nbv_start)
        pdc = pr["pdc_rate"] * (nbv_start - dep_t / 2)
        fixed = R * (dep_t + pdc + pf["maintenance_per_year"])
        detail = dict(depreciation=R * dep_t, pdc=R * pdc, maintenance=R * pf["maintenance_per_year"])
    elif m == "lease":
        fixed = R * (pf["lease_per_year"] + pf.get("maintenance_per_year", 0))
        detail = dict(lease=R * pf["lease_per_year"], maintenance=R * pf.get("maintenance_per_year", 0))
    elif m == "managed_service":
        included = pf["cases_included"] * contract_multiplier(cfg)
        excess = max(0.0, total_cases - included) * pf["excess_fee_per_case"]
        fixed = R * pf["annual_fee"] + excess
        detail = dict(annual_fee=R * pf["annual_fee"], excess_fees=excess)
        if pf.get("instruments_included"):
            instruments = 0.0
    elif m == "per_procedure":
        minimum = pf["minimum_cases_per_year"] * contract_multiplier(cfg)
        billable = max(total_cases, minimum)
        fixed = billable * pf["fee_per_case"]
        detail = dict(procedure_fees=fixed)
        if pf.get("instruments_included"):
            instruments = 0.0
    else:
        raise ValueError(f"unknown procurement model {m}")
    return dict(fixed=fixed, instruments=instruments, detail=detail)


def year_costs(cfg, t, tot, one_offs=True):
    """Every extra cost to the trust in year t for event totals `tot`.
    No 30-day cost avoided is deducted here."""
    pr, uc, R = cfg["programme"], cfg["unit_costs"], cfg["robots"]
    pc = platform_cost_year(cfg, t, tot["cases"])
    first = one_offs and t == 1
    c = dict(
        platform_fixed=pc["fixed"], platform_detail=pc["detail"], instruments=pc["instruments"],
        decontamination=tot["cases"] * uc.get("decontamination_per_case", 0.0),
        staffing=R * pr.get("sfa_wte_per_robot", 0.0) * pr.get("sfa_cost_per_wte", 0.0),
        theatre_time_cost=tot["extra_minutes"] * uc["theatre_minute"],
        implementation=R * pr["implementation_cost_per_robot"] if first else 0.0,
        theatre_modification=R * pr.get("theatre_modification_per_robot", 0.0) if first else 0.0,
    )
    c["gross_cost"] = (c["platform_fixed"] + c["instruments"] + c["decontamination"] + c["staffing"]
                       + c["theatre_time_cost"] + c["implementation"] + c["theatre_modification"])
    return c


def economic_cash_flows(cfg, yearly):
    """Discounted cash view for the economic case (Green Book): capital at
    year 0, residual net book value credited at the horizon; depreciation
    and PDC are excluded because they are not cash. 30-day cost avoided is
    deducted here (economic view)."""
    pf, pr, R, H = cfg["platform"], cfg["programme"], cfg["robots"], cfg["programme"]["horizon_years"]
    r = pr["discount_rate"]
    flows = []
    year0 = 0.0
    net_cap = 0.0
    if pf["model"] == "purchase":
        net_cap = pf["capital"] - pf.get("trade_in", 0)
        year0 = R * net_cap
    for y in yearly:
        t = y["year"]
        platform_cash = R * pf["maintenance_per_year"] if pf["model"] == "purchase" else y["platform_fixed"]
        cash = (platform_cash + y["implementation"] + y["theatre_modification"] + y["instruments"]
                + y["decontamination"] + y["staffing"] + y["theatre_time_cost"] - y["offsets"])
        if pf["model"] == "purchase" and t == H:
            dep = net_cap / pf["asset_life_years"]
            cash -= max(net_cap - dep * H, 0) * R
        flows.append(dict(year=t, cash=cash, discounted=cash / (1 + r) ** t))
    npc = year0 + sum(f["discounted"] for f in flows)
    return dict(year0_capital=year0, flows=flows, net_present_cost=npc)


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------
TOTAL_EVENT_KEYS = EVENT_KEYS + ["cases", "open_avoided", "lap_displaced", "robot_elsewhere", "extra_minutes"]


def _sum_events(cfg, cases_by_group, mult):
    tot = {k: 0.0 for k in TOTAL_EVENT_KEYS}
    by_group = {}
    for k, g in cfg["groups"].items():
        ev = consequences(g, cases_by_group.get(k, 0.0), mult)
        by_group[k] = ev
        for key in tot:
            tot[key] += ev.get(key, 0.0)
    return tot, by_group


def run(cfg):
    pr, uc = cfg["programme"], cfg["unit_costs"]
    warnings = []
    f = fortnights_per_year(cfg)
    fixed = cfg.get("fixed_cases")      # benchmark profiles: annual cases given directly
    tsum = None
    if fixed is not None:
        cases_full = {k: float(fixed.get(k, 0.0)) for k in cfg["groups"]}
        cap = booked = 0
        sessions = {k: 0 for k in cfg["groups"]}
    else:
        tsum = T.summarise(cfg)
        cap, booked = tsum["available"], tsum["booked"]
        real = pr.get("realisation_factor", 1.0)
        cases_full = {k: tsum["cases_per_fortnight"][k] * f * real for k in cfg["groups"]}
        sessions = tsum["group_sessions"]
        for msg in tsum["issues"]:
            warnings.append(f"Rota: {msg}")
    total = sum(cases_full.values())
    cap_cases = pr.get("max_cases_per_robot", 700) * cfg["robots"]
    if total > cap_cases + 1e-6:
        warnings.append(f"Planned activity of {total:,.0f} cases a year is above "
                        f"{pr.get('max_cases_per_robot', 700):,} cases per robot (advisory): check surgeon numbers, "
                        "staffing and whether the lists are achievable.")
    if cfg["platform"].get("illustrative"):
        warnings.append(f"{cfg['platform']['label']}: the price is illustrative; enter the trust's quote.")
    groups_out = {k: dict(label=g["label"], specialty=g["specialty"], benefit_status=g["benefit_status"],
                          benefit_modelled=g["benefit_status"] != "not_yet_modelled",
                          sessions_per_fortnight=sessions[k], planned_cases=cases_full[k])
                  for k, g in cfg["groups"].items()}
    nm = {k: v["planned_cases"] for k, v in groups_out.items()
          if v["benefit_status"] == "not_yet_modelled" and v["planned_cases"] >= 0.5}
    if nm:
        warnings.append("30-day benefit not yet modelled for " + ", ".join(
            f"{cfg['groups'][k]['label']} ({v:,.0f} cases a year)" for k, v in nm.items())
            + ": their benefit is a zero placeholder pending evidence, not a finding that the robot has no benefit.")

    yearly = []
    for t in range(1, pr["horizon_years"] + 1):
        util = pr["utilisation_by_year"][t - 1]
        mult = cfg["evidence_multiplier"] * pr["learning_benefit_by_year"][t - 1]
        tot, by_group = _sum_events(cfg, {k: v * util for k, v in cases_full.items()}, mult)
        offsets = offsets_value(tot, uc)
        c = year_costs(cfg, t, tot)
        extra_cases = tot["bed_days"] / pr["mean_elective_los_for_capacity"]
        cap_value = extra_cases * pr["contribution_per_extra_case"] if pr.get("include_capacity_value") else 0.0
        offsets += cap_value
        tariff = sum(ev["cases"] * cfg["groups"][k].get("tariff_uplift", 0.0) for k, ev in by_group.items())
        yearly.append(dict(capacity_value=cap_value, year=t, utilisation=util, benefit_multiplier=mult, **tot,
                           tariff_income=tariff, net_cash_cost=c["gross_cost"] - tariff,
                           extra_elective_cases_enabled=extra_cases, **c,
                           extra_cost=c["gross_cost"],
                           offsets=offsets, net_cost=c["gross_cost"] - offsets,
                           extra_cost_per_case=c["gross_cost"] / tot["cases"] if tot["cases"] else None,
                           net_cost_per_case=(c["gross_cost"] - offsets) / tot["cases"] if tot["cases"] else None,
                           by_group=by_group))

    util_booked = booked / cap if cap else 0.0
    if fixed is None:
        if util_booked < pr["low_utilisation_warning"]:
            warnings.append(f"Booked utilisation {util_booked:.0%} is below the "
                            f"{pr['low_utilisation_warning']:.0%} threshold: book more sessions or reduce the "
                            "sessions available.")
        spare = cap - booked
        if spare >= 1:
            warnings.append(f"{spare:g} available session{'s' if spare != 1 else ''} per fortnight left "
                            "unfilled on the rota.")

    sum_keys = ["cases", "open_avoided", "robot_elsewhere"] + EVENT_KEYS + [
        "extra_elective_cases_enabled", "capacity_value", "gross_cost", "offsets", "net_cost",
        "platform_fixed", "instruments", "decontamination", "staffing", "theatre_time_cost",
        "implementation", "theatre_modification", "tariff_income", "net_cash_cost"]
    totals = {k: sum(y[k] for y in yearly) for k in sum_keys}
    totals["extra_cost"] = totals["gross_cost"]

    def ratio(num, x):
        return num / x if x > 1e-9 else None
    serious = totals["reoperations"] + totals["complications"] + totals["readmissions"]
    totals["cost_per_case"] = ratio(totals["extra_cost"], totals["cases"])
    totals["cost_per_open_operation_avoided"] = ratio(totals["extra_cost"], totals["open_avoided"])
    totals["cost_per_bed_day_released"] = ratio(totals["extra_cost"], totals["bed_days"])
    totals["cost_per_serious_event_avoided"] = ratio(totals["extra_cost"], serious)
    totals["net_cost_per_case"] = ratio(totals["net_cost"], totals["cases"])
    totals["net_cost_per_open_operation_avoided"] = ratio(totals["net_cost"], totals["open_avoided"])
    totals["net_cost_per_bed_day_released"] = ratio(totals["net_cost"], totals["bed_days"])
    totals["net_cost_per_serious_event_avoided"] = ratio(totals["net_cost"], serious)

    pf = cfg["platform"]
    capital = dict(total=cfg["robots"] * pf.get("capital", 0) if pf["model"] == "purchase" else 0.0,
                   trust_funded=cfg["robots"] * trust_capital(cfg) if pf["model"] == "purchase" else 0.0,
                   central=(cfg["robots"] * min(pr.get("central_capital_per_robot", 0),
                                                max(pf.get("capital", 0) - pf.get("trade_in", 0), 0))
                            if pf["model"] == "purchase" else 0.0))
    return dict(price_targets=price_targets(cfg, yearly),
                guardrails=spend_guardrails(cfg, groups_out, util_booked, yearly),
                config=cfg, grid=tsum["cells"] if tsum else [],
                input_mode="fixed" if fixed is not None else "rota", template_summary=tsum, groups=groups_out,
                capacity_per_fortnight=cap, booked_sessions_per_fortnight=booked,
                spare_sessions_per_fortnight=max(cap - booked, 0), booked_utilisation=util_booked,
                cases_per_robot=yearly[min(3, len(yearly)) - 1]["cases"] / cfg["robots"],
                yearly=yearly, totals=totals, economic=economic_cash_flows(cfg, yearly), capital=capital,
                break_even=break_even(cfg, cases_full, booked, cap), user_modified=modified_priors(cfg),
                warnings=warnings)


# ---------------------------------------------------------------------------
# 8. Break-even (steady state: full utilisation and full learning), searched
#    only up to the programme's maximum deliverable volume.
# ---------------------------------------------------------------------------
def steady_state_net(cfg, cases_by_group, scale):
    """Net annual cost at steady state (no one-off costs) when every group's
    planned cases are multiplied by `scale` (case mix held constant)."""
    pr, uc = cfg["programme"], cfg["unit_costs"]
    tot, _ = _sum_events(cfg, {k: v * scale for k, v in cases_by_group.items()}, cfg["evidence_multiplier"])
    c = year_costs(cfg, min(3, pr["horizon_years"]), tot, one_offs=False)
    cap_value = (tot["bed_days"] / pr["mean_elective_los_for_capacity"] * pr["contribution_per_extra_case"]
                 if pr.get("include_capacity_value") else 0.0)
    return c["gross_cost"] - offsets_value(tot, uc) - cap_value, tot["cases"]


def max_deliverable_cases(cfg, base_cases, booked_sessions, capacity=None):
    """The most cases a year the programme could deliver at this case mix: every
    available session used at the planned cases per session. (The 700-per-robot
    figure is advisory from v0.6.1 and does not limit this.)"""
    capacity = capacity or 0
    if booked_sessions and booked_sessions > 0:
        return base_cases * capacity / booked_sessions
    return base_cases


def break_even(cfg, cases_by_group, booked_sessions, capacity=None):
    base_net, base_cases = steady_state_net(cfg, cases_by_group, 1.0)
    if base_cases <= 0:
        return dict(status="no_cases", planned_cases=0, net_cost_at_plan=base_net, break_even_cases=None,
                    max_cases=None, note="No robotic cases planned.")
    max_cases = max_deliverable_cases(cfg, base_cases, booked_sessions, capacity)
    max_scale = max(max_cases / base_cases, 1.0)
    net_max, _ = steady_state_net(cfg, cases_by_group, max_scale)
    margin = (steady_state_net(cfg, cases_by_group, 2.0)[0] - base_net) / base_cases
    out = dict(planned_cases=base_cases, net_cost_at_plan=base_net, max_cases=max_cases,
               net_cost_at_max=net_max, marginal_net_cost_per_extra_case=margin, break_even_cases=None)
    if base_net <= 0:
        out.update(status="already", break_even_cases=None,
                   note="At the planned volume, 30-day cost avoided already covers the extra cost.")
        return out
    if margin >= 0:
        out.update(status="none", note=("No break-even volume: at this case mix each extra case adds more cost "
                                         "than it avoids at 30 days."))
        return out
    if net_max > 0:
        out.update(status="beyond_capacity",
                   note=(f"Not reachable within capacity: even at the maximum of about {max_cases:,.0f} cases a "
                         f"year, 30-day cost avoided would not cover the extra cost (shortfall "
                         f"£{net_max:,.0f} a year)."))
        return out
    lo, hi = 1.0, max_scale
    for _ in range(100):
        mid = (lo + hi) / 2
        if steady_state_net(cfg, cases_by_group, mid)[0] > 0:
            lo = mid
        else:
            hi = mid
    out.update(status="within_capacity", break_even_cases=hi * base_cases,
               note=f"30-day cost avoided would cover the extra cost at about {hi * base_cases:,.0f} cases a year.")
    return out


# ---------------------------------------------------------------------------
# Price targets (reverse calculation) and spend guardrails
# ---------------------------------------------------------------------------
def price_targets(cfg, yearly, target_per_bed_day=None):
    """Instrument price per case that would achieve (a) budget neutrality and
    (b) a target net cost per bed-day released, at the planned steady-state
    volume (year 3). Net cost is linear in instrument price, so
    price_needed = current_price - (net - target_net) / cases."""
    pf = cfg["platform"]
    charged = not pf.get("instruments_included", False) and pf["model"] != "per_procedure"
    y = yearly[min(3, len(yearly)) - 1]
    if not charged or y["cases"] == 0:
        return dict(applicable=False, note="Instruments are not charged separately under this model.")
    p0 = pf["instruments_per_case"]

    def needed(target_net):
        p = p0 - (y["net_cost"] - target_net) / y["cases"]
        return p if p >= 0 else None

    tpb = target_per_bed_day if target_per_bed_day is not None else cfg["programme"].get("target_net_cost_per_bed_day", 1500)
    return dict(applicable=True, current_price=p0, list_price=pf.get("instruments_list_price", p0),
                budget_neutral_price=needed(0.0),
                target_net_cost_per_bed_day=tpb,
                price_for_target=needed(tpb * y["bed_days"]),
                note="None means the target cannot be reached even at zero instrument cost.")


def spend_guardrails(cfg, groups_out, util, yearly):
    """Traffic-light checks that the money is being spent well."""
    pr = cfg["programme"]
    y = yearly[min(3, len(yearly)) - 1]
    out = []

    def add(name, value, status, rule):
        out.append(dict(check=name, value=value, status=status, rule=rule))

    per_robot = y["cases"] / cfg["robots"]
    capr = pr.get("max_cases_per_robot", 700)
    add("Robotic cases per robot per year", f"{per_robot:,.0f}", "green" if per_robot <= capr else "amber",
        f"Advisory: above {capr:,} a year, check surgeon numbers, staffing and whether the lists are achievable.")
    nm = [g["label"].split(" (")[0] for g in groups_out.values()
          if g["benefit_status"] == "not_yet_modelled" and g["planned_cases"] >= 0.5]
    add("Procedures with 30-day benefit not yet modelled", (", ".join(nm) if nm else "None"),
        "amber" if nm else "green",
        "Their 30-day benefit is a zero placeholder pending evidence, not a finding that the robot has no benefit; "
        "patient consequences and cost per outcome understate them.")
    add("Robot utilisation (sessions booked / available)", f"{util:.0%}",
        "green" if util >= 0.85 else "amber" if util >= pr["low_utilisation_warning"] else "red",
        "Green 85% or more; red below 75%.")
    share_open = y["open_avoided"] / y["cases"] if y["cases"] else 0
    add("Share of robotic cases displacing open surgery (advisory)", f"{share_open:.0%}",
        "green" if share_open >= 0.40 else "amber",
        "Advisory only. Green 40% or more, otherwise amber. Depends on the counterfactual entered by the trust.")
    s = cfg.get("instrument_price_setting", "list")
    add("Instrument price basis", D.INSTRUMENT_PRICE_LABELS.get(s, s),
        "green" if s in ("volume_discount", "custom") else "amber" if s == "standard_discount" else "red",
        "Red at supplier list price; amber at a standard discount; green at a volume discount or a trust quote.")
    illus = cfg["platform"].get("illustrative", False)
    add("Platform price", "Illustrative" if illus else "Published anchor", "red" if illus else "green",
        "Replace illustrative prices with a formal quote before approval.")
    mods = modified_priors(cfg)
    add("Assumptions changed from defaults", str(len(mods)),
        "green" if not mods else "amber", "Any change is listed in the appendix.")
    return out


# ---------------------------------------------------------------------------
# Flat assumption table (one row per procedure and comparator) for the web
# interface and the business case appendix
# ---------------------------------------------------------------------------
PRIOR_COLS = ["los", "conv", "reop", "comp", "readm", "extra_minutes"]


def prior_rows(cfg):
    rows = []
    for k, g in cfg["groups"].items():
        rows.append(dict(group=k, specialty=g["label"], comparator="open", share=g["p_open"],
                         los=g["los_reduction_open"], conv=0.0, reop=g["reop_reduction_open"],
                         comp=g["comp_reduction_open"], readm=g["readm_reduction_open"],
                         extra_minutes=g["extra_minutes_open"]))
        pe = g.get("p_robot_elsewhere", 0.0)
        if pe:
            rows.append(dict(group=k, specialty=g["label"], comparator="robot_elsewhere", share=pe,
                             los=0.0, conv=0.0, reop=0.0, comp=0.0, readm=0.0, extra_minutes=0.0))
        rows.append(dict(group=k, specialty=g["label"], comparator="conventional_mis",
                         share=1 - g["p_open"] - pe, los=g["los_reduction_lap"], conv=g["conv_reduction_lap"],
                         reop=g["reop_reduction_lap"], comp=g["comp_reduction_lap"],
                         readm=g["readm_reduction_lap"], extra_minutes=g["extra_minutes_lap"]))
    return rows


def overrides_from_prior_rows(rows):
    """Inverse of prior_rows: turn an edited table back into group overrides."""
    out = {}
    for row in rows:
        k, c = row["group"], row["comparator"]
        o = out.setdefault(k, {})
        if c == "robot_elsewhere":
            o.update(p_robot_elsewhere=float(row["share"]))
        elif c == "open":
            o.update(p_open=float(row["share"]), los_reduction_open=float(row["los"]),
                     reop_reduction_open=float(row["reop"]), comp_reduction_open=float(row["comp"]),
                     readm_reduction_open=float(row["readm"]), extra_minutes_open=float(row["extra_minutes"]))
        else:
            o.update(los_reduction_lap=float(row["los"]), conv_reduction_lap=float(row["conv"]),
                     reop_reduction_lap=float(row["reop"]), comp_reduction_lap=float(row["comp"]),
                     readm_reduction_lap=float(row["readm"]), extra_minutes_lap=float(row["extra_minutes"]))
    return out


# ---------------------------------------------------------------------------
# Readable description of a changed assumption (no internal keys)
# ---------------------------------------------------------------------------
def describe_item(cfg, item):
    parts = item.split(".")
    if parts[0] == "unit_costs":
        return D.UNIT_COST_LABELS.get(parts[1], parts[1].replace("_", " "))
    if parts[0] == "programme":
        return {"sfa_cost_per_wte": "Surgical first assistant: cost per WTE",
                "sfa_wte_per_robot": "Surgical first assistant: WTE per robot"}.get(parts[1], parts[1])
    g = cfg["groups"].get(parts[0]) or D.PROCEDURE_GROUPS.get(parts[0])
    name = g["label"] if g else parts[0]
    return f"{name}: {D.FIELD_LABELS.get(parts[1], parts[1].replace('_', ' '))}"


def fmt_value(v):
    """Readable value for a changed assumption."""
    if isinstance(v, bool):
        return "yes" if v else "no"
    return v if isinstance(v, str) else f"{v:g}"
