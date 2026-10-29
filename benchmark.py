"""
Benchmark profile: a well-functioning multi-port programme (about 550 cases per
robot per year, mid-level costs, typical case mix), run through the same engine
and shown side by side with the trust's proposal.

Every benchmark value carries a source in defaults.BENCHMARK["sources"]; values
with no published source are labelled as assumptions. The benchmark uses the same
30-day clinical assumptions and unit costs as the trust's case, so differences
reflect volume, case mix and price, not different clinical beliefs.
"""
import copy

import defaults as D
import engine as E

SPECIALTY_OF = {k: g["specialty"] for k, g in D.PROCEDURE_GROUPS.items()}


def benchmark_cases(spec=None):
    """Annual cases per procedure group for the benchmark programme."""
    b = spec or D.BENCHMARK
    total = b["cases_per_robot"] * b["robots"]
    shares = b["specialty_shares"]
    norm = sum(shares.values())
    out = {k: 0.0 for k in D.PROCEDURE_GROUPS}
    for spec_name, share in shares.items():
        for g, w in b["within_specialty"][spec_name].items():
            out[g] = total * share / norm * w
    return out


def benchmark_config(trust_cfg=None, spec=None):
    """Engine configuration for the benchmark. If the trust's configuration is
    given, its 30-day clinical assumptions, unit costs and programme settings
    (other than capital source) are reused for multi-port groups."""
    b = spec or D.BENCHMARK
    central = b["central_capital_per_robot"]
    if central is None:
        central = (trust_cfg or {}).get("programme", {}).get("central_capital_per_robot", 0)
    cfg = E.build_config("large_1", b["platform"], (trust_cfg or {}).get("evidence", "central"),
                         overrides={"robots": b["robots"],
                                    "programme": {"central_capital_per_robot": central}},
                         instrument_price=b["instrument_price"], template=None)
    if trust_cfg is not None:
        for k, g in trust_cfg["groups"].items():
            if k in cfg["groups"] and not E.is_multi_comparator(g):
                for f in D.BENEFIT_KEYS + ["p_open", "p_robot_elsewhere", "extra_minutes_open",
                                           "extra_minutes_lap"]:
                    cfg["groups"][k][f] = g.get(f, cfg["groups"][k].get(f, 0.0))
        cfg["unit_costs"] = copy.deepcopy(trust_cfg["unit_costs"])
        keep = {"central_capital_per_robot": central}
        cfg["programme"] = dict(copy.deepcopy(trust_cfg["programme"]), **keep)
    cases = benchmark_cases(b)
    for k, g in cfg["groups"].items():
        g["volume"] = cases.get(k, 0.0)
    cfg["fixed_cases"] = cases
    cfg["preset_label"] = b["label"]
    E.validate(cfg)
    return cfg


def run_benchmark(trust_cfg=None, spec=None):
    return E.run(benchmark_config(trust_cfg, spec))


def specialty_mix(result):
    """Share of steady-state cases by specialty (year 3)."""
    y = result["yearly"][min(3, len(result["yearly"])) - 1]
    tot = y["cases"] or 1.0
    mix = {}
    for k, ev in y["by_group"].items():
        sp = result["config"]["groups"][k]["specialty"]
        mix[sp] = mix.get(sp, 0.0) + ev["cases"] / tot
    return mix


def comparison_rows(trust, bench):
    """Side-by-side rows: (measure, trust value, benchmark value, benchmark source).
    Per-robot figures make programmes of different size comparable."""
    def y3(r):
        return r["yearly"][min(3, len(r["yearly"])) - 1]

    def per_robot(r, key):
        return y3(r)[key] / r["config"]["robots"]

    def money(x):
        return "n/a" if x is None else f"£{x:,.0f}"

    src = D.BENCHMARK["sources"]
    tm, bm = specialty_mix(trust), specialty_mix(bench)
    def mix_str(m):
        uro = m.get("Urology", 0)
        gen = sum(m.get(x, 0) for x in ("Colorectal", "Abdo wall complex", "Oesophagogastric",
                                         "Hepatopancreatobiliary"))
        gyn = m.get("Women's health", 0)
        other = max(1 - uro - gen - gyn, 0)
        return f"{uro:.0%} / {gen:.0%} / {gyn:.0%} / {other:.0%}"

    rows = [
        ("Robots", str(trust["config"]["robots"]), str(bench["config"]["robots"]), "Benchmark set at one robot."),
        ("Robotic cases per robot per year (year 3)", f"{trust['cases_per_robot']:,.0f}",
         f"{bench['cases_per_robot']:,.0f}", src["cases_per_robot"]),
        ("Case mix: urology / general surgery / women's health / other", mix_str(tm), mix_str(bm),
         src["specialty_shares"] + " Split within specialties: " + src["within_specialty"][0].lower()
         + src["within_specialty"][1:]),
        ("Open operations avoided per robot per year", f"{per_robot(trust, 'open_avoided'):,.0f}",
         f"{per_robot(bench, 'open_avoided'):,.0f}", src["clinical"]),
        ("Bed-days released per robot per year", f"{per_robot(trust, 'bed_days'):,.0f}",
         f"{per_robot(bench, 'bed_days'):,.0f}", src["clinical"]),
        ("Extra cost per robot per year (year 3)", money(per_robot(trust, "extra_cost")),
         money(per_robot(bench, "extra_cost")), src["platform"]),
        ("Extra cost per robotic case (five years)", money(trust["totals"]["cost_per_case"]),
         money(bench["totals"]["cost_per_case"]), "Calculated by the tool from the rows above."),
        ("Extra cost per open operation avoided", money(trust["totals"]["cost_per_open_operation_avoided"]),
         money(bench["totals"]["cost_per_open_operation_avoided"]), "Calculated by the tool."),
        ("Extra cost per bed-day released", money(trust["totals"]["cost_per_bed_day_released"]),
         money(bench["totals"]["cost_per_bed_day_released"]), "Calculated by the tool."),
    ]
    return rows
