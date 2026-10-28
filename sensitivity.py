"""
One-way sensitivity analysis (tornado).

Each assumption is moved, on its own, to a low and a high value while every other
input stays at the base case and the theatre template (or list plan) is held fixed. The change in the
chosen result is recorded. Ranges are placeholders for expert review unless a
source is given; they are listed in every output.

This replaces the v0.4 single multiplier on all benefits, which could not show
which assumption drives the result.
"""
import copy

import defaults as D
import engine as E

METRICS = {
    "extra_cost": ("Five-year extra cost to the trust", "£"),
    "cost_per_bed_day": ("Extra cost per bed-day released", "£"),
    "cost_per_open": ("Extra cost per open operation avoided", "£"),
    "npc": ("Net present cost to the NHS (economic view)", "£"),
    "net_cash": ("Five-year cash cost to the trust after tariff income", "£"),
}


def metric_value(r, metric):
    t = r["totals"]
    if metric == "extra_cost":
        return t["extra_cost"]
    if metric == "cost_per_bed_day":
        return t["cost_per_bed_day_released"]
    if metric == "cost_per_open":
        return t["cost_per_open_operation_avoided"]
    if metric == "npc":
        return r["economic"]["net_present_cost"]
    if metric == "net_cash":
        return t["net_cash_cost"]
    raise ValueError(metric)


# --- mutations: each takes (cfg, level) with level "low" or "high" and edits cfg in place
def _scale_groups(cfg, fields_mp, sp_key, factor):
    for g in cfg["groups"].values():
        if E.is_multi_comparator(g):
            for c in g["reductions"]:
                if sp_key == "extra_minutes":
                    g["extra_minutes"][c] *= factor
                else:
                    for k in sp_key:
                        g["reductions"][c][k] *= factor
        else:
            for f in fields_mp:
                g[f] *= factor


def _p_open(cfg, factor):
    for g in cfg["groups"].values():
        if E.is_multi_comparator(g):
            sh = g["comparators"]
            if "open" not in sh:
                continue
            new_open = min(sh["open"] * factor, 1.0)
            rest = 1.0 - sh["open"]
            scale = (1.0 - new_open) / rest if rest > 0 else 0.0
            g["comparators"] = {c: (new_open if c == "open" else v * scale) for c, v in sh.items()}
        else:
            g["p_open"] = min(g["p_open"] * factor, 1.0 - g.get("p_robot_elsewhere", 0.0))


def parameters(cfg):
    """List of (name, low description, high description, mutate(cfg, level)) applicable to cfg."""
    pf, pr = cfg["platform"], cfg["programme"]
    P = []

    def add(name, lo, hi, fn):
        P.append(dict(name=name, low=lo, high=hi, fn=fn))

    if pf["model"] == "purchase":
        add("Capital per robot", "-20%", "+20%",
            lambda c, l: c["platform"].__setitem__("capital", c["platform"]["capital"] * (0.8 if l == "low" else 1.2)))
    if pf["model"] in ("purchase", "lease") and pf.get("maintenance_per_year", 0):
        add("Maintenance per robot", "-20%", "+20%",
            lambda c, l: c["platform"].__setitem__("maintenance_per_year",
                                                   c["platform"]["maintenance_per_year"] * (0.8 if l == "low" else 1.2)))
    if pf["model"] == "lease":
        add("Lease per robot", "-20%", "+20%",
            lambda c, l: c["platform"].__setitem__("lease_per_year",
                                                   c["platform"]["lease_per_year"] * (0.8 if l == "low" else 1.2)))
    if pf["model"] == "managed_service":
        add("Managed service fee", "-20%", "+20%",
            lambda c, l: c["platform"].__setitem__("annual_fee", c["platform"]["annual_fee"] * (0.8 if l == "low" else 1.2)))
    if pf["model"] == "per_procedure":
        add("Fee per procedure", "-20%", "+20%",
            lambda c, l: c["platform"].__setitem__("fee_per_case", c["platform"]["fee_per_case"] * (0.8 if l == "low" else 1.2)))
    charged = not pf.get("instruments_included", False) and pf["model"] != "per_procedure"
    if charged and pf.get("instruments_per_case", 0):
        lp = pf.get("instruments_list_price", pf["instruments_per_case"])
        if cfg.get("instrument_price_setting") == "custom":
            add("Instrument price per case", "-20%", "+20%",
                lambda c, l: c["platform"].__setitem__("instruments_per_case",
                                                       c["platform"]["instruments_per_case"] * (0.8 if l == "low" else 1.2)))
        else:
            add("Instrument price per case", "30% off list", "list price",
                lambda c, l, lp=lp: c["platform"].__setitem__("instruments_per_case", lp * (0.7 if l == "low" else 1.0)))
    add("Sterile services per case", "half", "double",
        lambda c, l: c["unit_costs"].__setitem__("decontamination_per_case",
                                                 c["unit_costs"].get("decontamination_per_case", 0) * (0.5 if l == "low" else 2.0)))
    add("Surgical first assistant per robot", "0 WTE", "2 WTE",
        lambda c, l: c["programme"].__setitem__("sfa_wte_per_robot", 0.0 if l == "low" else 2.0))
    add("Extra theatre minutes per case", "-50%", "+50%",
        lambda c, l: _scale_groups(c, ["extra_minutes_open", "extra_minutes_lap"], "extra_minutes",
                                   0.5 if l == "low" else 1.5))
    add("Cost per theatre minute", "£8", "£20",
        lambda c, l: c["unit_costs"].__setitem__("theatre_minute", 8 if l == "low" else 20))
    if cfg.get("template") is not None:
        add("Share of templated cases that go ahead", "85%", "100%",
            lambda c, l: c["programme"].__setitem__("realisation_factor", 0.85 if l == "low" else 1.0))
    add("Steady-state utilisation", "80%", "100%",
        lambda c, l: c["programme"].__setitem__(
            "utilisation_by_year",
            [u if i < 2 else (0.8 if l == "low" else 1.0) for i, u in enumerate(c["programme"]["utilisation_by_year"])]))
    add("Share open without the robot (all specialties)", "half", "1.5 times", lambda c, l: _p_open(c, 0.5 if l == "low" else 1.5))
    add("Bed-days saved per case", "half", "1.5 times",
        lambda c, l: _scale_groups(c, ["los_reduction_open", "los_reduction_lap"], ["los"], 0.5 if l == "low" else 1.5))
    add("Complications, returns to theatre, readmissions and conversions avoided", "half", "1.5 times",
        lambda c, l: _scale_groups(c, [k for k in D.BENEFIT_KEYS if not k.startswith("los")],
                                   ["conv", "reop", "comp", "readm"], 0.5 if l == "low" else 1.5))
    add("Learning curve (years 1 and 2)", "slower (50%, 75%)", "none (100%)",
        lambda c, l: c["programme"].__setitem__(
            "learning_benefit_by_year",
            ([0.5, 0.75] if l == "low" else [1.0, 1.0]) + list(c["programme"]["learning_benefit_by_year"][2:])))
    add("Excess bed-day cost", "£250", "£800",
        lambda c, l: c["unit_costs"].__setitem__("bed_day", 250 if l == "low" else 800))
    g = cfg["groups"].get("prostatectomy")
    if g is not None and g["volume"] > 0 and not E.is_multi_comparator(g):
        def prost(c, l):
            if l == "high":
                c["groups"]["prostatectomy"]["p_open"] = 0.0
                c["groups"]["prostatectomy"]["p_robot_elsewhere"] = 1.0
        add("Prostatectomy comparator", "open (base)", "robotic at another centre", prost)
    return P


def tornado(cfg, metric="extra_cost", base_result=None):
    """Bars sorted by swing. Each bar: name, low/high labels and values, swing."""
    base = base_result or E.run(cfg)
    base_val = metric_value(base, metric)
    bars, no_effect = [], []
    for p in parameters(cfg):
        vals = {}
        for level in ("low", "high"):
            c = copy.deepcopy(cfg)
            if base.get("input_mode") == "demand":
                c["manual_plan"] = dict(base["plan"])
            p["fn"](c, level)
            E.validate(c)
            vals[level] = metric_value(E.run(c), metric)
        if vals["low"] is None or vals["high"] is None or base_val is None:
            continue
        swing = abs(vals["high"] - vals["low"])
        if swing < 0.5:
            no_effect.append(p["name"])
            continue
        bars.append(dict(name=p["name"], low_label=p["low"], high_label=p["high"],
                         low=vals["low"], high=vals["high"], swing=swing))
    bars.sort(key=lambda b: -b["swing"])
    return dict(metric=metric, metric_label=METRICS[metric][0], base=base_val, bars=bars, no_effect=no_effect)
