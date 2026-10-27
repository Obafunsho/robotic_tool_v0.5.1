"""
Robotic programme decision engine: 30-day cost-consequence analysis.

Pipeline (each step is a small, separately testable function):
  1. demand ceiling      ceiling_g = annual robotic cases available_g (one step)
  2. capacity            sessions/yr = robots x sessions_per_week x weeks
  3. fortnightly plan    whole dedicated lists (each at least min_list_fill full) plus
                         shared half-day sessions that pool the remaining demand
  4. cases               dedicated + shared cases, capped at max_cases_per_robot x robots,
                         then x util_t
  5. counterfactual      open_g = cases x p_open ; elsewhere_g = cases x p_robot_elsewhere ;
                         lap_g = the rest (shares are what would happen WITHOUT the robot)
  6. 30-day consequences events avoided = displaced cases x reduction x evidence x learning_t
  7. extra cost          platform + instruments + sterile services + surgical first assistant
                         + extra theatre time + one-off implementation and theatre works
                         (the headline: no deduction for bed-days or other 30-day offsets)
  8. cost avoided        events avoided x unit costs (economic view only; not cash)
  9. net of cost avoided 7 - 8, by year (financial) and discounted (economic)
 10. break-even          volume at which 7 - 8 = 0 at steady state, searched only up to the
                         programme's maximum deliverable volume

No QALYs and no ICERs are computed, by design.
"""
from __future__ import annotations

import copy
import math

import defaults as D

EVENT_KEYS = ["bed_days", "conversions", "reoperations", "complications", "readmissions"]


# ---------------------------------------------------------------------------
# 0. Configuration
# ---------------------------------------------------------------------------
def build_config(preset="medium_dgh_1", platform="platform_b", evidence="central",
                 overrides=None, plan=None, instrument_price="list"):
    """Assemble a full input set from defaults, then apply user overrides.

    overrides = {"groups": {gkey: {field: value}}, "unit_costs": {...},
                 "programme": {...}, "platform": {...}, "robots": int}
    plan      = {gkey: sessions_per_fortnight}  (manual plan; None = automatic)
    """
    p = D.PRESETS[preset]
    sp = D.PLATFORMS[platform].get("procedure_set") == "single_port"
    groups = copy.deepcopy(D.SP_GROUPS if sp else D.PROCEDURE_GROUPS)
    for g in groups.values():
        g["volume"] = g[p["volume_key"]]
    cfg = dict(
        preset=preset, preset_label=p["label"], robots=p["robots"],
        evidence=evidence, evidence_multiplier=D.EVIDENCE_SETTINGS[evidence],
        groups=groups, unit_costs=copy.deepcopy(D.UNIT_COSTS),
        programme=copy.deepcopy(D.PROGRAMME),
        platform_key=platform, platform=copy.deepcopy(D.PLATFORMS[platform]),
        manual_plan=copy.deepcopy(plan), version=D.ENGINE_VERSION,
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
    # instrument price setting: a named setting multiplies the platform price;
    # a number replaces it outright (the trust's quote)
    pf = cfg["platform"]
    pf["instruments_list_price"] = pf.get("instruments_per_case", 0)
    if isinstance(instrument_price, (int, float)):
        pf["instruments_per_case"] = float(instrument_price)
        cfg["instrument_price_setting"] = "custom"
    else:
        pf["instruments_per_case"] = pf["instruments_list_price"] * D.INSTRUMENT_PRICE_SETTINGS[instrument_price]
        cfg["instrument_price_setting"] = instrument_price
    validate(cfg)
    return cfg


def is_multi_comparator(g):
    return "comparators" in g


def validate(cfg):
    for gk, g in cfg["groups"].items():
        if is_multi_comparator(g):
            sh = g["comparators"]
            if any(v < 0 for v in sh.values()) or abs(sum(sh.values()) - 1) > 1e-6:
                raise ValueError(f"{gk}: comparator shares must be >=0 and sum to 1")
            for c in sh:
                if any(g["reductions"][c][k] < 0 for k in D.SP_REDUCTION_KEYS):
                    raise ValueError(f"{gk}.{c}: reductions are entered as positive numbers")
        else:
            pe = g.get("p_robot_elsewhere", 0.0)
            if not 0 <= g["p_open"] <= 1 or not 0 <= pe <= 1 or g["p_open"] + pe > 1 + 1e-9:
                raise ValueError(f"{g['label']}: the open and robot-elsewhere shares must each lie between "
                                 f"0 and 1 and together not exceed 1")
        if g["volume"] < 0 or g["cases_per_list"] <= 0 or g["list_sessions"] not in (1, 2):
            raise ValueError(f"{gk}: cases must be >=0, cases_per_list >0, list_sessions 1 or 2")
        for k in ([] if is_multi_comparator(g) else D.BENEFIT_KEYS):
            if g[k] < 0:
                raise ValueError(f"{gk}.{k}: reductions are entered as positive numbers")
    pr = cfg["programme"]
    if len(pr["utilisation_by_year"]) < pr["horizon_years"]:
        raise ValueError("utilisation_by_year shorter than horizon")
    if len(pr["learning_benefit_by_year"]) < pr["horizon_years"]:
        raise ValueError("learning_benefit_by_year shorter than horizon")
    if cfg["robots"] < 1:
        raise ValueError("robots must be >= 1")
    if pr.get("max_cases_per_robot", 700) <= 0:
        raise ValueError("max_cases_per_robot must be positive")
    basis = cfg["platform"].get("contract_volume_basis", "per_robot")
    if basis not in ("per_robot", "per_contract"):
        raise ValueError("contract_volume_basis must be 'per_robot' or 'per_contract'")


def modified_priors(cfg):
    """List every benefit prior or unit cost that differs from the locked defaults."""
    out = []
    for gk, g in cfg["groups"].items():
        if is_multi_comparator(g):
            ref = D.SP_GROUPS[gk]
            for c, v in g["comparators"].items():
                if v != ref["comparators"].get(c):
                    out.append(dict(item=f"{gk}.share.{c}", default=ref["comparators"].get(c), used=v))
                for k in D.SP_REDUCTION_KEYS:
                    if g["reductions"][c][k] != ref["reductions"][c][k]:
                        out.append(dict(item=f"{gk}.{c}.{k}", default=ref["reductions"][c][k],
                                        used=g["reductions"][c][k]))
                if g["extra_minutes"][c] != ref["extra_minutes"][c]:
                    out.append(dict(item=f"{gk}.{c}.extra_minutes", default=ref["extra_minutes"][c],
                                    used=g["extra_minutes"][c]))
            if g["cases_per_list"] != ref["cases_per_list"]:
                out.append(dict(item=f"{gk}.cases_per_list", default=ref["cases_per_list"], used=g["cases_per_list"]))
            continue
        for k in D.BENEFIT_KEYS + ["p_open", "p_robot_elsewhere", "cases_per_list",
                                   "extra_minutes_open", "extra_minutes_lap"]:
            if g.get(k, 0.0) != D.PROCEDURE_GROUPS[gk].get(k, 0.0):
                out.append(dict(item=f"{gk}.{k}", default=D.PROCEDURE_GROUPS[gk].get(k, 0.0), used=g.get(k, 0.0)))
    for k, v in cfg["unit_costs"].items():
        if v != D.UNIT_COSTS[k]:
            out.append(dict(item=f"unit_costs.{k}", default=D.UNIT_COSTS[k], used=v))
    return out


# ---------------------------------------------------------------------------
# 1-3. Demand, capacity and the fortnightly plan
# ---------------------------------------------------------------------------
def ceiling_cases(g):
    return g["volume"]


def cases_per_session(g):
    return g["cases_per_list"] / g["list_sessions"]


def fortnights_per_year(cfg):
    return cfg["programme"]["operating_weeks_per_year"] / 2


def capacity_per_fortnight(cfg):
    return cfg["robots"] * cfg["programme"]["sessions_per_robot_per_week"] * 2


def required_sessions_per_fortnight(cfg, g):
    return ceiling_cases(g) / cases_per_session(g) / fortnights_per_year(cfg)


def robots_needed(cfg):
    """Robots needed to meet the full demand ceiling of all groups."""
    req = sum(required_sessions_per_fortnight(cfg, g) for g in cfg["groups"].values())
    per_robot = cfg["programme"]["sessions_per_robot_per_week"] * 2
    return dict(fractional=req / per_robot, whole=math.ceil(req / per_robot - 1e-9),
                demand_sessions_per_fortnight=req)


def offset_per_case(cfg, g):
    """Steady-state cost avoided per robotic case at full learning (used for ranking)."""
    return offsets_value(consequences(g, 1.0, cfg["evidence_multiplier"]), cfg["unit_costs"])


SHARED = "_shared"     # plan key for shared (pooled) half-day sessions


def shared_label():
    return "Shared list (pooled smaller specialties)"


def slot_label(cfg, key, short=True):
    if key == SHARED:
        return "Shared" if short else shared_label()
    g = cfg["groups"][key]
    return g["specialty"] if short else g["label"]


def lists_needed(cfg, g):
    """Lists per fortnight needed to meet the group's full demand (fractional)."""
    return required_sessions_per_fortnight(cfg, g) / g["list_sessions"]


def dedicated_cases(cfg, g, sessions_per_fortnight):
    raw = sessions_per_fortnight * fortnights_per_year(cfg) * cases_per_session(g)
    return min(raw, ceiling_cases(g)), raw


def shared_need(cfg, plan):
    """Shared sessions per fortnight needed to absorb every group's residual demand."""
    need = {}
    for k, g in cfg["groups"].items():
        ded, _ = dedicated_cases(cfg, g, plan.get(k, 0))
        resid = max(ceiling_cases(g) - ded, 0.0)
        need[k] = resid / cases_per_session(g) / fortnights_per_year(cfg)
    return need


def shared_sessions_for(need_total, spare, threshold):
    """Whole shared half-day sessions to offer: never more than spare capacity and
    never so many that the shared list would be less than `threshold` full."""
    if need_total <= 1e-9 or spare <= 0:
        return 0
    if need_total >= spare:
        return int(spare)
    return int(min(spare, math.floor(need_total / threshold + 1e-9)))


def auto_plan(cfg, rule=None):
    """Sessions per fortnight, in whole lists (half-day list = 1 session, all-day = 2).

    a) A group gets a dedicated list only if that list would be at least
       min_list_fill full (default 75%), NHSE-priority groups first.
    b) Further dedicated lists, each again at least min_list_fill full, go one at a
       time to the least-filled group relative to its demand ("proportional"), or to
       the group with the highest 30-day cost avoided per session ("benefit").
    c) Remaining capacity is offered as shared half-day sessions that pool every
       group's leftover demand, again only if the shared sessions would be at least
       min_list_fill full. Spare sessions are left empty and reported.
    """
    rule = rule or cfg["programme"].get("allocation_rule", "proportional")
    thr = cfg["programme"].get("min_list_fill", 0.75)
    cap = capacity_per_fortnight(cfg)
    G = cfg["groups"]
    L = {k: lists_needed(cfg, g) for k, g in G.items()}
    alloc = {k: 0 for k in G}
    used = 0
    order = sorted(G, key=lambda k: (not G[k]["nhse_priority"], k))
    for k in order:
        blk = G[k]["list_sessions"]
        if L[k] >= thr - 1e-9 and used + blk <= cap:
            alloc[k] = blk
            used += blk
    value = {k: offset_per_case(cfg, g) * cases_per_session(g) for k, g in G.items()}
    while True:
        cands = [k for k in G if alloc[k] and L[k] - alloc[k] / G[k]["list_sessions"] >= thr - 1e-9
                 and used + G[k]["list_sessions"] <= cap]
        if not cands:
            break
        if rule == "benefit":
            best = max(cands, key=lambda k: (value[k], k))
        else:
            best = min(cands, key=lambda k: ((alloc[k] / G[k]["list_sessions"]) / L[k], k))
        alloc[best] += G[best]["list_sessions"]
        used += G[best]["list_sessions"]
    alloc[SHARED] = shared_sessions_for(sum(shared_need(cfg, alloc).values()), cap - used, thr)
    return alloc


def normalise_plan(cfg, plan):
    out = {k: int(plan.get(k, 0)) for k in cfg["groups"]}
    out[SHARED] = int(plan.get(SHARED, 0))
    return out


def delivered_cases(cfg, plan):
    """Annual cases per group at full utilisation: dedicated lists plus a share of
    the shared sessions, then capped at max_cases_per_robot x robots.
    Returns (per-group dict, summary dict)."""
    f = fortnights_per_year(cfg)
    need = shared_need(cfg, plan)
    need_total = sum(need.values())
    S = plan.get(SHARED, 0)
    out = {}
    for k, g in cfg["groups"].items():
        ded, raw = dedicated_cases(cfg, g, plan.get(k, 0))
        if S and need_total > 1e-12:
            sess = need[k] if need_total <= S else S * need[k] / need_total
        else:
            sess = 0.0
        out[k] = dict(dedicated=ded, raw_dedicated=raw, shared=sess * f * cases_per_session(g),
                      shared_sessions=sess)
    total = sum(v["dedicated"] + v["shared"] for v in out.values())
    cap_cases = cfg["programme"].get("max_cases_per_robot", 700) * cfg["robots"]
    scale = min(1.0, cap_cases / total) if total > 0 else 1.0
    for v in out.values():
        v["total"] = (v["dedicated"] + v["shared"]) * scale
    shared_fill = (min(need_total / S, 1.0) if S else None)
    return out, dict(total_before_cap=total, cap_cases=cap_cases, cap_scale=scale,
                     shared_sessions=S, shared_fill=shared_fill)


def fortnight_grid(cfg, plan):
    """Lay the plan out as robot x week x day x AM/PM. All-day lists are placed
    first on days with both sessions free; half-day lists, then shared sessions,
    fill the rest. With 9 sessions per week, Friday PM is left free for maintenance."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    spw = cfg["programme"]["sessions_per_robot_per_week"]
    slots = []
    for r in range(1, cfg["robots"] + 1):
        for w in (1, 2):
            n = 0
            for d in days:
                for s in ("AM", "PM"):
                    if n < spw:
                        slots.append(dict(robot=r, week=w, day=d, session=s, group=None))
                    n += 1
    G = cfg["groups"]
    full = [k for k in G if G[k]["list_sessions"] == 2 for _ in range(plan.get(k, 0) // 2)]
    half = [k for k in G if G[k]["list_sessions"] == 1 for _ in range(plan.get(k, 0))]
    half += [SHARED] * plan.get(SHARED, 0)
    i = 0
    while i < len(slots) - 1 and full:
        a, b = slots[i], slots[i + 1]
        if (a["group"] is None and b["group"] is None and a["session"] == "AM"
                and (a["robot"], a["week"], a["day"]) == (b["robot"], b["week"], b["day"])):
            k = full.pop(0)
            a["group"] = b["group"] = k
            i += 2
        else:
            i += 1
    for slot in slots:
        if slot["group"] is None and half:
            slot["group"] = half.pop(0)
    unplaced = len(full) * 2 + len(half)
    return slots if not unplaced else slots + [dict(robot=None, week=None, day=None,
                                                    session=f"UNPLACED x{unplaced}", group=None)]


# ---------------------------------------------------------------------------
# 4-6. Cases and 30-day patient consequences
# ---------------------------------------------------------------------------
def planned_cases(cfg, g, sessions_per_fortnight):
    """Dedicated-list cases only (kept for backwards compatibility)."""
    return dedicated_cases(cfg, g, sessions_per_fortnight)


def consequences(g, cases, multiplier):
    """Events avoided for a given number of robotic cases. multiplier =
    evidence setting x learning-curve factor for the year."""
    m = multiplier
    if is_multi_comparator(g):
        ev = dict(cases=cases, open_avoided=0.0, lap_displaced=0.0, robot_elsewhere=0.0, bed_days=0.0,
                  conversions=0.0, reoperations=0.0, complications=0.0, readmissions=0.0, extra_minutes=0.0)
        for c, share in g["comparators"].items():
            n = cases * share
            r = g["reductions"][c]
            if c in D.OPEN_LIKE:
                ev["open_avoided"] += n
            else:
                ev["lap_displaced"] += n
            ev["bed_days"] += m * n * r["los"]
            ev["conversions"] += m * n * r["conv"]
            ev["reoperations"] += m * n * r["reop"]
            ev["complications"] += m * n * r["comp"]
            ev["readmissions"] += m * n * r["readm"]
            ev["extra_minutes"] += n * g["extra_minutes"][c]
        return ev
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
# 7. Platform costs
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
# 8-9. Full run
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
    cap = capacity_per_fortnight(cfg)
    f = fortnights_per_year(cfg)
    thr = pr.get("min_list_fill", 0.75)
    fixed = cfg.get("fixed_cases")            # benchmark profiles: delivered cases given directly

    if fixed is not None:
        plan = normalise_plan(cfg, {})
        dc = {k: dict(dedicated=0.0, raw_dedicated=0.0, shared=0.0, shared_sessions=0.0,
                      total=float(fixed.get(k, 0.0))) for k in cfg["groups"]}
        cap_cases = pr.get("max_cases_per_robot", 700) * cfg["robots"]
        tot_fixed = sum(v["total"] for v in dc.values())
        if tot_fixed > cap_cases:
            for v in dc.values():
                v["total"] *= cap_cases / tot_fixed
        summ = dict(total_before_cap=tot_fixed, cap_cases=cap_cases, cap_scale=min(1.0, cap_cases / tot_fixed)
                    if tot_fixed else 1.0, shared_sessions=0, shared_fill=None)
        booked = sum(v["total"] / cases_per_session(cfg["groups"][k]) for k, v in dc.items()) / f
    else:
        plan = cfg["manual_plan"] if cfg["manual_plan"] is not None else auto_plan(cfg)
        plan = normalise_plan(cfg, plan)
        dc, summ = delivered_cases(cfg, plan)
        booked = sum(plan.values())
    if booked > cap + 1e-9 and fixed is None:
        warnings.append(f"The plan books {booked:g} sessions per fortnight but capacity is {cap}.")
    if summ["cap_scale"] < 1.0:
        warnings.append(f"Planned activity of {summ['total_before_cap']:,.0f} cases a year exceeds the cap of "
                        f"{pr.get('max_cases_per_robot', 700):,} cases per robot; cases were scaled down to "
                        f"{summ['cap_cases']:,.0f}.")
    if cfg["platform"].get("illustrative"):
        warnings.append(f"{cfg['platform']['label']}: the price is illustrative; enter the trust's quote.")

    groups_out = {}
    for k, g in cfg["groups"].items():
        d = dc[k]
        fill = None
        if plan.get(k):
            fill = min(d["raw_dedicated"], ceiling_cases(g)) / d["raw_dedicated"] if d["raw_dedicated"] else 0.0
            if fill < thr - 1e-9:
                warnings.append(f"{g['label']}: its lists would be only {fill:.0%} full "
                                f"({g['cases_per_list']:g} cases per list); consider fewer lists.")
        if plan.get(k, 0) % g["list_sessions"]:
            warnings.append(f"{g['label']}: all-day lists need sessions in pairs.")
        unmet = max(ceiling_cases(g) - d["total"], 0.0)
        if fixed is None and unmet >= 0.5:
            has_lists = bool(plan.get(k)) or d["shared"] >= 0.5
            if summ["cap_scale"] < 1.0:
                why = f"the cap of {pr.get('max_cases_per_robot', 700):,} cases per robot is reached"
            elif booked >= cap:
                why = ("robot capacity is fully booked" if has_lists
                       else "robot capacity is fully booked by other specialties")
            else:
                why = ("the remaining demand is too small to fill another list at least "
                       f"{thr:.0%} full" if has_lists else
                       "too few to fill a regular list. Consider pooling with another site")
            sched = (f"{d['total']:,.0f} of {ceiling_cases(g):,.0f} scheduled" if has_lists
                     else "none scheduled")
            warnings.append(f"{g['label']}: {unmet:,.0f} cases a year are not scheduled ({sched}); {why}.")
        groups_out[k] = dict(label=g["label"], sessions_per_fortnight=plan.get(k, 0),
                             ceiling=ceiling_cases(g), dedicated_cases=d["dedicated"],
                             shared_cases=d["shared"], planned_cases=d["total"], unmet_cases=unmet,
                             list_fill=fill)

    cases_full = {k: v["planned_cases"] for k, v in groups_out.items()}
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
        yearly.append(dict(capacity_value=cap_value, year=t, utilisation=util, benefit_multiplier=mult, **tot,
                           extra_elective_cases_enabled=extra_cases, **c,
                           extra_cost=c["gross_cost"],
                           offsets=offsets, net_cost=c["gross_cost"] - offsets,
                           extra_cost_per_case=c["gross_cost"] / tot["cases"] if tot["cases"] else None,
                           net_cost_per_case=(c["gross_cost"] - offsets) / tot["cases"] if tot["cases"] else None,
                           by_group=by_group))

    util_booked = booked / cap if cap else 0
    if util_booked < pr["low_utilisation_warning"]:
        warnings.append(f"Booked utilisation {util_booked:.0%} is below the "
                        f"{pr['low_utilisation_warning']:.0%} threshold: consider fewer robots "
                        "or more specialties.")
    spare = cap - booked
    unmet_all = sum(g["unmet_cases"] for g in groups_out.values())
    if fixed is None and spare >= 1:
        why = ("all demand entered is already scheduled" if unmet_all < 0.5 else
               f"the remaining demand ({unmet_all:,.0f} cases a year) is too small to fill another list at "
               f"least {thr:.0%} full")
        warnings.append(f"{spare:g} session{'s' if spare != 1 else ''} per fortnight left unbooked: {why}.")

    sum_keys = ["cases", "open_avoided", "robot_elsewhere"] + EVENT_KEYS + [
        "extra_elective_cases_enabled", "capacity_value", "gross_cost", "offsets", "net_cost",
        "platform_fixed", "instruments", "decontamination", "staffing", "theatre_time_cost",
        "implementation", "theatre_modification"]
    totals = {k: sum(y[k] for y in yearly) for k in sum_keys}
    totals["extra_cost"] = totals["gross_cost"]

    def ratio(num, x):
        return num / x if x > 1e-9 else None
    serious = totals["reoperations"] + totals["complications"] + totals["readmissions"]
    # Cost per outcome: extra cost to the trust (no offsets) divided by each consequence.
    totals["cost_per_case"] = ratio(totals["extra_cost"], totals["cases"])
    totals["cost_per_open_operation_avoided"] = ratio(totals["extra_cost"], totals["open_avoided"])
    totals["cost_per_bed_day_released"] = ratio(totals["extra_cost"], totals["bed_days"])
    totals["cost_per_serious_event_avoided"] = ratio(totals["extra_cost"], serious)
    # Economic view: net of 30-day cost avoided. Descriptive, not additive.
    totals["net_cost_per_case"] = ratio(totals["net_cost"], totals["cases"])
    totals["net_cost_per_open_operation_avoided"] = ratio(totals["net_cost"], totals["open_avoided"])
    totals["net_cost_per_bed_day_released"] = ratio(totals["net_cost"], totals["bed_days"])
    totals["net_cost_per_serious_event_avoided"] = ratio(totals["net_cost"], serious)

    mods = modified_priors(cfg)
    prices = price_targets(cfg, yearly)
    guard = spend_guardrails(cfg, plan, groups_out, util_booked, yearly, warnings)
    pf = cfg["platform"]
    capital = dict(total=cfg["robots"] * pf.get("capital", 0) if pf["model"] == "purchase" else 0.0,
                   trust_funded=cfg["robots"] * trust_capital(cfg) if pf["model"] == "purchase" else 0.0,
                   central=(cfg["robots"] * min(pr.get("central_capital_per_robot", 0),
                                                max(pf.get("capital", 0) - pf.get("trade_in", 0), 0))
                            if pf["model"] == "purchase" else 0.0))
    return dict(price_targets=prices, guardrails=guard,
                config=cfg, plan=plan, grid=fortnight_grid(cfg, plan), groups=groups_out,
                capacity_per_fortnight=cap, booked_sessions_per_fortnight=booked,
                spare_sessions_per_fortnight=max(spare, 0), shared=summ,
                booked_utilisation=util_booked, robots_needed=robots_needed(cfg),
                cases_per_robot=yearly[min(3, len(yearly)) - 1]["cases"] / cfg["robots"],
                yearly=yearly, totals=totals, economic=economic_cash_flows(cfg, yearly), capital=capital,
                break_even=break_even(cfg, cases_full, booked), user_modified=mods,
                unmet_cases=sum(g["unmet_cases"] for g in groups_out.values()),
                warnings=warnings)


# ---------------------------------------------------------------------------
# 10. Break-even (steady state: full utilisation and full learning), searched
#     only up to the programme's maximum deliverable volume.
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


def max_deliverable_cases(cfg, base_cases, booked_sessions):
    """The most cases a year the programme could deliver at this case mix: the
    lower of the per-robot cap and full use of every session at the planned
    cases per session."""
    hard_cap = cfg["programme"].get("max_cases_per_robot", 700) * cfg["robots"]
    if booked_sessions and booked_sessions > 0:
        by_sessions = base_cases * capacity_per_fortnight(cfg) / booked_sessions
        return min(hard_cap, by_sessions)
    return hard_cap


def break_even(cfg, cases_by_group, booked_sessions):
    base_net, base_cases = steady_state_net(cfg, cases_by_group, 1.0)
    if base_cases <= 0:
        return dict(status="no_cases", planned_cases=0, net_cost_at_plan=base_net, break_even_cases=None,
                    max_cases=None, note="No robotic cases planned.")
    max_cases = max_deliverable_cases(cfg, base_cases, booked_sessions)
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
# 11. Price targets (reverse calculation) and spend guardrails
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


def spend_guardrails(cfg, plan, groups_out, util, yearly, warnings):
    """Traffic-light checks that the money is being spent well.
    Each returns status 'green', 'amber' or 'red' with the value tested."""
    pr = cfg["programme"]
    y = yearly[min(3, len(yearly)) - 1]
    out = []

    def add(name, value, status, rule):
        out.append(dict(check=name, value=value, status=status, rule=rule))

    add("Robot utilisation (booked sessions)", f"{util:.0%}",
        "green" if util >= 0.85 else "amber" if util >= pr["low_utilisation_warning"] else "red",
        "Green 85% or more; red below 75%.")
    share_open = y["open_avoided"] / y["cases"] if y["cases"] else 0
    add("Share of robotic cases displacing open surgery (advisory)", f"{share_open:.0%}",
        "green" if share_open >= 0.40 else "amber",
        "Advisory only. Green 40% or more, otherwise amber. Depends on the counterfactual entered by the trust.")
    thr = pr.get("min_list_fill", 0.75)
    short = [g["label"] for g in groups_out.values()
             if g["sessions_per_fortnight"] and g["list_fill"] is not None and g["list_fill"] < thr - 1e-9]
    add("Lists less than 75% full", str(len(short)),
        "green" if not short else "amber",
        "Every dedicated list should be at least 75% full; the automatic plan never creates one that is not.")
    s = cfg.get("instrument_price_setting", "list")
    add("Instrument price basis", D.INSTRUMENT_PRICE_LABELS.get(s, s),
        "green" if s in ("volume_discount", "custom") else "amber" if s == "standard_discount" else "red",
        "Red at supplier list price; amber at a standard discount; green at a volume discount or a trust quote.")
    illus = cfg["platform"].get("illustrative", False)
    add("Platform price", "Illustrative" if illus else "Published anchor", "red" if illus else "green",
        "Replace illustrative prices with a formal quote before approval.")
    expl = cfg["platform"].get("exploratory", False)
    add("Platform evidence base", "Exploratory" if expl else "Established", "amber" if expl else "green",
        "Exploratory platforms have limited comparative evidence and little UK use.")
    mods = modified_priors(cfg)
    add("Benefit assumptions changed from defaults", str(len(mods)),
        "green" if not mods else "amber", "Any change is listed in the appendix.")
    return out


# ---------------------------------------------------------------------------
# 12. Flat assumption table (one row per specialty and comparator) for the
#     web interface and the business case appendix; works for both maths.
# ---------------------------------------------------------------------------
PRIOR_COLS = ["los", "conv", "reop", "comp", "readm", "extra_minutes"]


def prior_rows(cfg):
    rows = []
    for k, g in cfg["groups"].items():
        if is_multi_comparator(g):
            for c, share in g["comparators"].items():
                r = g["reductions"][c]
                rows.append(dict(group=k, specialty=g["label"], comparator=c, share=share,
                                 los=r["los"], conv=r["conv"], reop=r["reop"], comp=r["comp"],
                                 readm=r["readm"], extra_minutes=g["extra_minutes"][c]))
        else:
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


def overrides_from_prior_rows(rows, platform):
    """Inverse of prior_rows: turn an edited table back into group overrides."""
    sp = D.PLATFORMS[platform].get("procedure_set") == "single_port"
    out = {}
    for row in rows:
        k, c = row["group"], row["comparator"]
        if sp:
            o = out.setdefault(k, dict(comparators={}, reductions={}, extra_minutes={}))
            o["comparators"][c] = float(row["share"])
            o["reductions"][c] = {x: float(row[x]) for x in D.SP_REDUCTION_KEYS}
            o["extra_minutes"][c] = float(row["extra_minutes"])
        else:
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
# 13. Human-readable description of a changed assumption (no internal keys)
# ---------------------------------------------------------------------------
def describe_item(cfg, item):
    parts = item.split(".")
    if parts[0] == "unit_costs":
        return D.UNIT_COST_LABELS.get(parts[1], parts[1].replace("_", " "))
    g = cfg["groups"].get(parts[0]) or D.PROCEDURE_GROUPS.get(parts[0]) or D.SP_GROUPS.get(parts[0])
    name = g["label"] if g else parts[0]
    if len(parts) == 3 and parts[1] == "share":
        return f"{name}: share {D.COMPARATOR_LABELS.get(parts[2], parts[2]).lower()} without the robot"
    if len(parts) == 3:
        return (f"{name}: {D.FIELD_LABELS.get(parts[2], parts[2])} versus "
                f"{D.COMPARATOR_LABELS.get(parts[1], parts[1]).lower()}")
    return f"{name}: {D.FIELD_LABELS.get(parts[1], parts[1].replace('_', ' '))}"
