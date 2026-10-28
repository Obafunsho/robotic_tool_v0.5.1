"""
Tests for the robotic programme decision engine (v0.5).

Layers:
  A. Hand-calculated toy case: every number worked out on paper (see comments).
  B. Invariants: properties that must hold for any valid input.
  C. Independent cross-check: cost avoided recomputed by a separate, naive
     implementation across every preset, platform and evidence setting.
  D. List planner: whole lists at least 75% full, shared list, spare capacity.
  E. Volume cap and break-even within deliverable capacity.
  F. Contract basis, robot-at-another-centre comparator, new cost lines.
  G. Benchmark, sensitivity (tornado), assumptions register, inputs reload.
  H. Business case builder and Word document.
  I. Single-port platform (different maths, same interface).
"""
import io
import itertools
import json
from pathlib import Path
import re

import pytest

import benchmark as BM
import business_case as BC
import defaults as D
import engine as E
import inputs_io as IO
import register as RG
import sensitivity as S
import templates as T

EX = Path(__file__).parent / "examples"


def legacy(preset="medium_dgh_1", platform="platform_b", evidence="central", **kw):
    """v0.5 demand-led planner (no theatre template)."""
    return E.build_config(preset, platform, evidence, template=None, **kw)


# ---------------------------------------------------------------------------
# A. Hand-calculated toy case
# ---------------------------------------------------------------------------
def toy_cfg(plan=None, **prog):
    """One robot, colorectal only, round numbers, new v0.5 cost lines set to zero."""
    zero = {k: {"volume": 0} for k in D.PROCEDURE_GROUPS if k != "colorectal"}
    groups = dict(zero, colorectal=dict(
        volume=100, cases_per_list=1, list_sessions=1, p_open=0.5,
        los_reduction_open=2, los_reduction_lap=1, conv_reduction_lap=0.1,
        reop_reduction_open=0.1, reop_reduction_lap=0,
        comp_reduction_open=0.1, comp_reduction_lap=0,
        readm_reduction_open=0.1, readm_reduction_lap=0,
        extra_minutes_open=10, extra_minutes_lap=10))
    programme = dict(sessions_per_robot_per_week=10, operating_weeks_per_year=40,
                     utilisation_by_year=[1] * 5, learning_benefit_by_year=[1] * 5,
                     implementation_cost_per_robot=0, theatre_modification_per_robot=0,
                     sfa_wte_per_robot=0, pdc_rate=0.0, discount_rate=0.10, horizon_years=5)
    programme.update(prog)
    return E.build_config(
        preset="medium_dgh_1", platform="platform_b", evidence="central",
        overrides=dict(
            groups=groups, programme=programme,
            unit_costs=dict(bed_day=100, reoperation=1000, major_complication=1000,
                            readmission=1000, conversion=1000, theatre_minute=10, decontamination_per_case=0),
            platform=dict(capital=1_000_000, trade_in=0, asset_life_years=5,
                          maintenance_per_year=100_000, instruments_per_case=1000)),
        plan=plan or {"colorectal": 5})


def test_toy_cases():
    # 5 sessions/fortnight x 20 fortnights x 1 case = 100 = ceiling
    r = E.run(toy_cfg())
    assert r["groups"]["colorectal"]["planned_cases"] == pytest.approx(100)
    y = r["yearly"][0]
    assert y["open_avoided"] == pytest.approx(50)
    assert y["lap_displaced"] == pytest.approx(50)


def test_toy_consequences():
    y = E.run(toy_cfg())["yearly"][0]
    assert y["bed_days"] == pytest.approx(50 * 2 + 50 * 1)   # 150
    assert y["conversions"] == pytest.approx(50 * 0.1)       # 5
    assert y["reoperations"] == pytest.approx(5)
    assert y["complications"] == pytest.approx(5)
    assert y["readmissions"] == pytest.approx(5)


def test_toy_costs():
    y = E.run(toy_cfg())["yearly"][0]
    assert y["offsets"] == pytest.approx(150 * 100 + 4 * 5 * 1000)   # 35,000
    assert y["theatre_time_cost"] == pytest.approx(100 * 10 * 10)    # 10,000
    assert y["instruments"] == pytest.approx(100 * 1000)             # 100,000
    assert y["platform_fixed"] == pytest.approx(200_000 + 100_000)   # dep + maintenance
    assert y["extra_cost"] == pytest.approx(410_000)                 # headline: no offsets
    assert y["net_cost"] == pytest.approx(410_000 - 35_000)          # 375,000
    assert y["extra_cost_per_case"] == pytest.approx(4_100)


def test_toy_five_year_and_ratios():
    t = E.run(toy_cfg())["totals"]
    assert t["extra_cost"] == pytest.approx(5 * 410_000)
    assert t["net_cost"] == pytest.approx(5 * 375_000)
    # cost per outcome uses the extra cost, not net of cost avoided
    assert t["cost_per_open_operation_avoided"] == pytest.approx(2_050_000 / 250)
    assert t["cost_per_bed_day_released"] == pytest.approx(2_050_000 / 750)
    assert t["net_cost_per_bed_day_released"] == pytest.approx(1_875_000 / 750)


def test_toy_economic_npc():
    # year 0 capital 1,000,000; annual cash = 100k + 100k + 10k - 35k = 175k
    e = E.run(toy_cfg())["economic"]
    annuity = sum(1 / 1.1 ** t for t in range(1, 6))
    assert e["net_present_cost"] == pytest.approx(1_000_000 + 175_000 * annuity)


def test_toy_pdc():
    # NBV start 1,000,000, depreciation 200,000, average NBV 900,000 -> PDC 31,500
    cfg = toy_cfg(pdc_rate=0.035)
    assert E.platform_cost_year(cfg, 1, 100)["detail"]["pdc"] == pytest.approx(31_500)
    assert E.platform_cost_year(cfg, 3, 100)["detail"]["pdc"] == pytest.approx(0.035 * 500_000)


def test_toy_new_cost_lines():
    # sterile services 100 x 50; first assistant 1.5 x 40,000; works 30,000 in year 1 only
    cfg = toy_cfg(sfa_wte_per_robot=1.5, sfa_cost_per_wte=40_000, theatre_modification_per_robot=30_000)
    cfg["unit_costs"]["decontamination_per_case"] = 50
    r = E.run(cfg)
    y1, y2 = r["yearly"][0], r["yearly"][1]
    assert y1["decontamination"] == pytest.approx(5_000)
    assert y1["staffing"] == pytest.approx(60_000)
    assert y1["theatre_modification"] == pytest.approx(30_000) and y2["theatre_modification"] == 0
    assert y1["extra_cost"] == pytest.approx(410_000 + 5_000 + 60_000 + 30_000)
    assert y2["extra_cost"] == pytest.approx(410_000 + 5_000 + 60_000)


# ---------------------------------------------------------------------------
# B. Invariants
# ---------------------------------------------------------------------------
MP_PLATFORMS = [k for k, v in D.PLATFORMS.items() if v.get("procedure_set") != "single_port"]
ALL = list(itertools.product(D.PRESETS, MP_PLATFORMS, D.EVIDENCE_SETTINGS))


@pytest.mark.parametrize("preset,platform,evidence", ALL)
def test_template_within_capacity_demand_and_cap(preset, platform, evidence):
    r = E.run(E.build_config(preset, platform, evidence))
    assert r["input_mode"] == "template"
    assert r["booked_sessions_per_fortnight"] <= r["capacity_per_fortnight"]
    for k, g in r["groups"].items():
        if k not in D.NOT_MODELLED:
            assert g["planned_cases"] <= r["config"]["groups"][k]["volume"] + 1e-6
    assert sum(1 for c in r["grid"] if c["status"] == "booked") == r["booked_sessions_per_fortnight"]


@pytest.mark.parametrize("preset,platform,evidence", ALL)
def test_plan_within_capacity_ceiling_and_cap(preset, platform, evidence):
    r = E.run(legacy(preset, platform, evidence))
    assert r["booked_sessions_per_fortnight"] <= r["capacity_per_fortnight"]
    for g in r["groups"].values():
        assert g["planned_cases"] <= g["ceiling"] + 1e-6
    filled = sum(1 for s in r["grid"] if s["group"])
    assert filled == r["booked_sessions_per_fortnight"]


@pytest.mark.parametrize("preset,platform,evidence", ALL)
def test_extra_cost_is_sum_of_parts_and_ignores_offsets(preset, platform, evidence):
    r = E.run(E.build_config(preset, platform, evidence))
    for y in r["yearly"]:
        parts = (y["platform_fixed"] + y["instruments"] + y["decontamination"] + y["staffing"]
                 + y["theatre_time_cost"] + y["implementation"] + y["theatre_modification"])
        assert y["extra_cost"] == pytest.approx(parts)
        assert y["net_cost"] == pytest.approx(y["extra_cost"] - y["offsets"])


@pytest.mark.parametrize("preset", D.PRESETS)
def test_no_benefit_means_no_offsets(preset):
    r = E.run(E.build_config(preset, "platform_b", "no_benefit"))
    assert all(y["offsets"] == 0 for y in r["yearly"])
    assert r["totals"]["bed_days"] == 0


@pytest.mark.parametrize("preset", D.PRESETS)
def test_offsets_scale_with_evidence_but_extra_cost_does_not(preset):
    plan = E.auto_plan(E.build_config(preset))
    cons = E.run(E.build_config(preset, evidence="conservative", plan=plan))
    cent = E.run(E.build_config(preset, evidence="central", plan=plan))
    assert cent["totals"]["offsets"] == pytest.approx(2 * cons["totals"]["offsets"])
    assert cent["totals"]["extra_cost"] == pytest.approx(cons["totals"]["extra_cost"])


def test_consequences_are_linear_in_cases():
    g = D.PROCEDURE_GROUPS["colorectal"]
    a, b = E.consequences(g, 100, 1.0), E.consequences(g, 200, 1.0)
    for k in E.EVENT_KEYS:
        assert b[k] == pytest.approx(2 * a[k])


def test_zero_volume_leaves_only_fixed_costs():
    zero = {k: {"volume": 0} for k in D.PROCEDURE_GROUPS}
    r = E.run(E.build_config(overrides={"groups": zero}))
    assert r["yearly"][2]["cases"] == 0     # template capped at zero demand
    r = E.run(legacy(overrides={"groups": zero}))
    y = r["yearly"][2]
    assert y["cases"] == 0 and y["offsets"] == 0 and y["instruments"] == 0
    assert y["extra_cost"] == pytest.approx(y["platform_fixed"] + y["staffing"])
    assert r["break_even"]["status"] == "no_cases"


def test_discount_zero_equals_cash_sum():
    e = E.run(toy_cfg(discount_rate=0.0))["economic"]
    assert e["net_present_cost"] == pytest.approx(1_000_000 + 5 * 175_000)


def test_user_modified_flag_and_readable_label():
    cfg = E.build_config(overrides={"groups": {"colorectal": {"los_reduction_open": 3.0}}})
    mods = E.modified_priors(cfg)
    assert any(m["item"] == "colorectal.los_reduction_open" and m["used"] == 3.0 for m in mods)
    assert E.describe_item(cfg, "colorectal.los_reduction_open") == \
        "Colorectal major resection (colon and rectum): bed-days saved versus open"
    assert E.describe_item(cfg, "unit_costs.bed_day") == "Excess bed-day"
    assert E.modified_priors(E.build_config()) == []


def test_validation_rejects_bad_inputs():
    with pytest.raises(ValueError):
        E.build_config(overrides={"groups": {"colorectal": {"p_open": 1.2}}})
    with pytest.raises(ValueError):
        E.build_config(overrides={"groups": {"colorectal": {"los_reduction_open": -1}}})
    with pytest.raises(ValueError):
        E.build_config(overrides={"groups": {"colorectal": {"p_open": 0.6, "p_robot_elsewhere": 0.6}}})
    with pytest.raises(ValueError):
        E.build_config(platform="platform_c", overrides={"platform": {"contract_volume_basis": "per_site"}})


def test_overbooked_manual_plan_warns():
    r = E.run(E.build_config(plan={"colorectal": 30}))
    assert any("capacity" in w for w in r["warnings"])


def test_underfilled_manual_list_warns():
    # 3 colorectal cases per all-day list with 40 cases: 6 sessions would be about 20% full
    cfg = E.build_config(overrides={"groups": {"colorectal": {"cases_per_list": 3, "volume": 40}}},
                         plan={"colorectal": 6})
    r = E.run(cfg)
    assert any("full" in w for w in r["warnings"])
    assert next(g for g in r["guardrails"] if g["check"] == "Lists less than 75% full")["status"] == "amber"


@pytest.mark.parametrize("inject", [1_000_000, 2_000_000])
def test_central_capital_injection(inject):
    base = E.run(E.build_config())
    cen = E.run(E.build_config(overrides={"programme": {"central_capital_per_robot": inject}}))
    cap = D.PLATFORMS["platform_b"]["capital"]
    life = D.PLATFORMS["platform_b"]["asset_life_years"]
    assert cen["yearly"][0]["platform_detail"]["depreciation"] == pytest.approx(max(cap - inject, 0) / life)
    assert cen["economic"]["net_present_cost"] == pytest.approx(base["economic"]["net_present_cost"])
    assert cen["capital"]["trust_funded"] == pytest.approx(max(cap - inject, 0))
    assert cen["capital"]["central"] + cen["capital"]["trust_funded"] == pytest.approx(cap)


@pytest.mark.parametrize("setting,mult", list(D.INSTRUMENT_PRICE_SETTINGS.items()))
def test_instrument_price_settings(setting, mult):
    cfg = E.build_config(instrument_price=setting)
    assert cfg["platform"]["instruments_per_case"] == pytest.approx(1500 * mult)
    assert E.build_config(instrument_price=900)["platform"]["instruments_per_case"] == 900


def test_price_targets_reproduce_target():
    ov = {"programme": {"central_capital_per_robot": 2_000_000}}
    r = E.run(E.build_config(overrides=ov))
    pt = r["price_targets"]
    for key, target in [("budget_neutral_price", 0.0),
                        ("price_for_target", pt["target_net_cost_per_bed_day"] * r["yearly"][2]["bed_days"])]:
        if pt[key] is not None:
            r2 = E.run(E.build_config(overrides=ov, instrument_price=pt[key], template=r["config"]["template"]))
            assert r2["yearly"][2]["net_cost"] == pytest.approx(target, abs=1e-6)


def test_guardrails_present_and_valid():
    g = E.run(E.build_config())["guardrails"]
    assert len(g) == 8 and all(x["status"] in ("green", "amber", "red") for x in g)


def test_capacity_value_toggle():
    off = E.run(E.build_config())
    on = E.run(E.build_config(overrides={"programme": {"include_capacity_value": True}}))
    y = on["yearly"][2]
    assert y["capacity_value"] == pytest.approx(y["extra_elective_cases_enabled"] * 1500)
    assert off["yearly"][2]["net_cost"] - y["net_cost"] == pytest.approx(y["capacity_value"])
    assert off["yearly"][2]["extra_cost"] == pytest.approx(y["extra_cost"])


# ---------------------------------------------------------------------------
# C. Independent cross-check (naive re-implementation of cost avoided)
# ---------------------------------------------------------------------------
def naive_offsets(cfg, r, year):
    uc, pr = cfg["unit_costs"], cfg["programme"]
    m = cfg["evidence_multiplier"] * pr["learning_benefit_by_year"][year - 1]
    u = pr["utilisation_by_year"][year - 1]
    total = 0.0
    for k, g in cfg["groups"].items():
        n = r["groups"][k]["planned_cases"] * u
        o = n * g["p_open"]
        l = n * (1 - g["p_open"] - g.get("p_robot_elsewhere", 0))
        total += m * uc["bed_day"] * (o * g["los_reduction_open"] + l * g["los_reduction_lap"])
        total += m * uc["conversion"] * l * g["conv_reduction_lap"]
        total += m * uc["reoperation"] * (o * g["reop_reduction_open"] + l * g["reop_reduction_lap"])
        total += m * uc["major_complication"] * (o * g["comp_reduction_open"] + l * g["comp_reduction_lap"])
        total += m * uc["readmission"] * (o * g["readm_reduction_open"] + l * g["readm_reduction_lap"])
    return total


@pytest.mark.parametrize("preset,platform,evidence", ALL)
def test_independent_offsets(preset, platform, evidence):
    cfg = E.build_config(preset, platform, evidence)
    r = E.run(cfg)
    for y in r["yearly"]:
        assert y["offsets"] == pytest.approx(naive_offsets(cfg, r, y["year"]))


def naive_delivered(cfg, plan):
    """Separate re-implementation of dedicated plus shared cases (before the cap)."""
    f = cfg["programme"]["operating_weeks_per_year"] / 2
    ded, resid = {}, {}
    for k, g in cfg["groups"].items():
        cps = g["cases_per_list"] / g["list_sessions"]
        ded[k] = min(plan.get(k, 0) * f * cps, g["volume"])
        resid[k] = (g["volume"] - ded[k]) / cps / f
    need = sum(resid.values())
    S_ = plan.get(E.SHARED, 0)
    out = {}
    for k, g in cfg["groups"].items():
        cps = g["cases_per_list"] / g["list_sessions"]
        share = 0 if not S_ or need == 0 else (resid[k] if need <= S_ else S_ * resid[k] / need)
        out[k] = ded[k] + share * f * cps
    return out


@pytest.mark.parametrize("preset", D.PRESETS)
def test_independent_delivered_cases(preset):
    cfg = legacy(preset)
    r = E.run(cfg)
    nd = naive_delivered(cfg, r["plan"])
    for k in cfg["groups"]:
        assert r["groups"][k]["planned_cases"] == pytest.approx(nd[k] * r["shared"]["cap_scale"])


# ---------------------------------------------------------------------------
# D. List planner
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("preset", D.PRESETS)
@pytest.mark.parametrize("rule", ["proportional", "benefit"])
def test_every_automatic_list_is_at_least_75_percent_full(preset, rule):
    cfg = legacy(preset)
    plan = E.auto_plan(cfg, rule)
    thr = cfg["programme"]["min_list_fill"]
    for k, g in cfg["groups"].items():
        n_lists = plan[k] / g["list_sessions"]
        assert plan[k] % g["list_sessions"] == 0
        if n_lists:
            # the last list must still be at least 75% full
            assert E.lists_needed(cfg, g) - (n_lists - 1) >= thr - 1e-9
    assert sum(plan.values()) <= E.capacity_per_fortnight(cfg)
    S_ = plan[E.SHARED]
    need = sum(E.shared_need(cfg, plan).values())
    if S_:
        assert min(need / S_, 1.0) >= thr - 1e-9


@pytest.mark.parametrize("preset", D.PRESETS)
def test_spare_sessions_only_when_another_list_would_be_underfilled(preset):
    cfg = legacy(preset)
    plan = E.auto_plan(cfg)
    spare = E.capacity_per_fortnight(cfg) - sum(plan.values())
    need = sum(E.shared_need(cfg, plan).values())
    if spare >= 1:
        assert need < (plan[E.SHARED] + 1) * cfg["programme"]["min_list_fill"] + 1e-9


def test_medium_dgh_regression_from_v04_review():
    # v0.4 left 3 sessions empty, about 10 hysterectomy patients unallocated, and created
    # colorectal and nephrectomy lists it then flagged as unfillable.
    # (v0.5 demand placeholders restored in v0.6.1, so the v0.5 plan is reproduced exactly)
    r = E.run(legacy("medium_dgh_1"))
    assert r["groups"]["hysterectomy"]["unmet_cases"] == pytest.approx(0, abs=0.5)
    assert r["unmet_cases"] == pytest.approx(0, abs=0.5)
    assert not any("only" in w and "full" in w for w in r["warnings"])
    assert r["booked_sessions_per_fortnight"] == 16 and r["plan"][E.SHARED] == 5
    assert r["shared"]["shared_fill"] == pytest.approx(4.0381 / 5, rel=1e-3)


def test_unmet_demand_warns_even_when_specialty_has_lists_template():
    r = E.run(E.build_config(overrides={"groups": {"colorectal": {"volume": 20000}}}))
    g = r["groups"]["colorectal"]
    assert g["template_cases"] > 0 and g["unmet_cases"] > 19_000
    w = [x for x in r["warnings"] if x.startswith("Colorectal major resection")]
    assert len(w) == 1 and f"{g['unmet_cases']:,.0f} cases a year are not scheduled" in w[0]
    assert "the template does not schedule enough cases" in w[0]


def test_unmet_demand_warns_even_when_specialty_has_lists():
    # v0.5.0 only warned for specialties with no lists: colorectal at 20,000 left about
    # 19,700 cases unscheduled with no warning.
    r = E.run(legacy(overrides={"groups": {"colorectal": {"volume": 20000}}}))
    g = r["groups"]["colorectal"]
    assert r["plan"]["colorectal"] > 0 and g["unmet_cases"] > 19_000
    w = [x for x in r["warnings"] if x.startswith("Colorectal major resection")]
    assert len(w) == 1 and f"{g['unmet_cases']:,.0f} cases a year are not scheduled" in w[0]
    assert f"{g['planned_cases']:,.0f} of 20,000 scheduled" in w[0] and "fully booked" in w[0]
    assert r["unmet_cases"] == pytest.approx(sum(x["unmet_cases"] for x in r["groups"].values()))


@pytest.mark.parametrize("preset", D.PRESETS)
@pytest.mark.parametrize("platform", ["platform_b", "platform_d"])
@pytest.mark.parametrize("template", ["standard", "extended", None])
def test_every_group_with_unmet_demand_has_one_warning(preset, platform, template):
    r = E.run(E.build_config(preset, platform, template=template))
    for k, g in r["groups"].items():
        hits = [w for w in r["warnings"] if w.startswith(g["label"] + ":") and "not scheduled" in w]
        assert len(hits) == (1 if g["unmet_cases"] >= 0.5 else 0), (g["label"], hits)


def test_unmet_demand_reason_when_robot_is_full():
    zero = {k: {"volume": 0} for k in D.PROCEDURE_GROUPS}
    zero["adnexal"] = {"volume": 2000}
    r = E.run(legacy(overrides={"groups": zero}))
    w = next(x for x in r["warnings"] if x.startswith("Adnexal surgery"))
    assert "785 cases a year are not scheduled" in w and "fully booked" in w and "cap of" not in w


def test_total_unmet_demand_in_business_case():
    case = {"cover": {}, "configuration": {"preset": "medium_dgh_1", "robots": 1, "platform": "platform_b",
                                           "groups": {"colorectal": {"volume": 20000}}}}
    blocks, r = BC.build_blocks(case, include_charts=False)
    assert f"Total unmet demand: {r['unmet_cases']:,.0f} cases a year" in all_text(blocks)


def test_shared_sessions_rule():
    assert E.shared_sessions_for(0.0, 5, 0.75) == 0
    assert E.shared_sessions_for(0.5, 5, 0.75) == 0      # one session would be 50% full
    assert E.shared_sessions_for(0.8, 5, 0.75) == 1
    assert E.shared_sessions_for(4.04, 7, 0.75) == 5     # 81% full
    assert E.shared_sessions_for(9.0, 3, 0.75) == 3      # demand exceeds spare: all used


def test_demand_above_capacity_fills_robot():
    cfg = legacy("large_1")
    assert sum(E.auto_plan(cfg).values()) == E.capacity_per_fortnight(cfg)


def test_grid_keeps_all_day_lists_together_and_places_shared():
    r = E.run(legacy("large_2"))
    by_day = {}
    for s in r["grid"]:
        if s["group"] and s["group"] != E.SHARED and r["config"]["groups"][s["group"]]["list_sessions"] == 2:
            by_day.setdefault((s["robot"], s["week"], s["day"]), []).append(s["group"])
    assert all(len(v) == 2 and v[0] == v[1] for v in by_day.values())
    assert sum(1 for s in r["grid"] if s["group"] == E.SHARED) == r["plan"][E.SHARED]


# ---------------------------------------------------------------------------
# E. Volume cap and break-even
# ---------------------------------------------------------------------------
def test_700_per_robot_is_advisory_not_a_cut():
    # v0.6.1: 3 adnexal cases per half-day list on every session = 18 x 22.5 x 3 = 1,215 a year,
    # above 700: flagged amber, not cut
    zero = {k: {"volume": 0} for k in D.PROCEDURE_GROUPS}
    zero["adnexal"] = {"volume": 2000}
    r = E.run(legacy(overrides={"groups": zero}))
    assert r["yearly"][2]["cases"] == pytest.approx(1215)
    assert any("above 700 cases per robot (advisory)" in w for w in r["warnings"])
    g = next(x for x in r["guardrails"] if x["check"] == "Robotic cases per robot per year")
    assert g["status"] == "amber" and g["value"] == "1,215"
    ok = next(x for x in E.run(E.build_config())["guardrails"] if x["check"] == "Robotic cases per robot per year")
    assert ok["status"] == "green"


def test_break_even_within_capacity():
    # bed-day 2,000: cost avoided per case = 1.5 x 2000 + 4 x 0.05 x 1000 = 3,200; variable 1,100
    # margin 2,100 per case; fixed 300,000 -> 142.857 cases, within the maximum of 400
    cfg = toy_cfg()
    cfg["unit_costs"]["bed_day"] = 2000
    be = E.run(cfg)["break_even"]
    assert be["status"] == "within_capacity"
    assert be["break_even_cases"] == pytest.approx(300_000 / 2_100, rel=1e-6)
    assert be["max_cases"] == pytest.approx(400)   # 100 cases on 5 of 20 sessions


def test_break_even_beyond_capacity_is_not_reported_as_a_number():
    # bed-day 1,000: cost avoided per case 1.5 x 1000 + 200 = 1,700; margin 600; break-even 500 cases,
    # beyond the 400 the sessions allow (100 cases on 5 of 20 sessions)
    cfg = toy_cfg()
    cfg["unit_costs"]["bed_day"] = 1000
    be = E.run(cfg)["break_even"]
    assert be["status"] == "beyond_capacity" and be["break_even_cases"] is None
    assert be["max_cases"] == pytest.approx(400)
    assert be["net_cost_at_max"] == pytest.approx(300_000 - 400 * 600)


def test_toy_no_break_even():
    # variable cost 1,100 per case exceeds cost avoided 350 per case
    be = E.run(toy_cfg())["break_even"]
    assert be["status"] == "none" and be["break_even_cases"] is None
    assert be["marginal_net_cost_per_extra_case"] == pytest.approx(750)


@pytest.mark.parametrize("preset,platform", list(itertools.product(D.PRESETS, MP_PLATFORMS)))
@pytest.mark.parametrize("capval", [False, True])
def test_break_even_never_exceeds_deliverable_volume(preset, platform, capval):
    cfg = E.build_config(preset, platform, "optimistic",
                         overrides={"programme": {"include_capacity_value": capval},
                                    "unit_costs": {"bed_day": 1198}})
    be = E.run(cfg)["break_even"]
    cap = cfg["programme"]["max_cases_per_robot"] * cfg["robots"]
    assert be["max_cases"] <= cap + 1e-6
    if be["break_even_cases"] is not None:
        assert be["break_even_cases"] <= be["max_cases"] + 1e-6


# ---------------------------------------------------------------------------
# F. Contract basis, robot elsewhere, cost lines
# ---------------------------------------------------------------------------
def test_managed_service_excess_fee_per_robot_and_per_contract():
    per_robot = E.build_config(platform="platform_c", overrides={"robots": 2})
    per_con = E.build_config(platform="platform_c", overrides={
        "robots": 2, "platform": {"contract_volume_basis": "per_contract"}})
    # 700 cases on 2 robots: per robot 600 included -> 100 excess; per contract 300 -> 400 excess
    assert E.platform_cost_year(per_robot, 1, 700)["detail"]["excess_fees"] == pytest.approx(100 * 1200)
    assert E.platform_cost_year(per_con, 1, 700)["detail"]["excess_fees"] == pytest.approx(400 * 1200)
    assert E.platform_cost_year(per_con, 1, 700)["fixed"] == pytest.approx(2 * 450_000 + 400 * 1200)


def test_per_procedure_minimum_per_robot_and_per_contract():
    cfg = E.build_config(platform="custom_per_procedure")
    assert E.platform_cost_year(cfg, 1, 100)["fixed"] == pytest.approx(300 * 2500)
    assert E.platform_cost_year(cfg, 1, 400)["fixed"] == pytest.approx(400 * 2500)
    two = E.build_config(platform="custom_per_procedure", overrides={"robots": 2})
    assert E.platform_cost_year(two, 1, 100)["fixed"] == pytest.approx(600 * 2500)
    con = E.build_config(platform="custom_per_procedure", overrides={
        "robots": 2, "platform": {"contract_volume_basis": "per_contract"}})
    assert E.platform_cost_year(con, 1, 100)["fixed"] == pytest.approx(300 * 2500)


def test_prostatectomy_open_is_default_comparator():
    g = D.PROCEDURE_GROUPS["prostatectomy"]
    assert g["p_open"] == 1.0 and g["p_robot_elsewhere"] == 0.0


def test_robot_elsewhere_has_no_30_day_difference():
    g = dict(D.PROCEDURE_GROUPS["prostatectomy"], p_open=0.0, p_robot_elsewhere=1.0)
    ev = E.consequences(g, 100, 1.0)
    assert ev["robot_elsewhere"] == 100 and ev["open_avoided"] == 0 and ev["lap_displaced"] == 0
    assert all(ev[k] == 0 for k in E.EVENT_KEYS) and ev["extra_minutes"] == 0


def test_prostatectomy_scenario_cuts_benefits_not_costs():
    base = E.run(E.build_config("large_1"))
    sc = E.run(E.build_config("large_1", template=base["config"]["template"],
                              overrides={"groups": BC.PROSTATE_ELSEWHERE}))
    assert sc["totals"]["bed_days"] < base["totals"]["bed_days"]
    assert sc["totals"]["open_avoided"] < base["totals"]["open_avoided"]
    assert sc["totals"]["extra_cost"] == pytest.approx(base["totals"]["extra_cost"])
    assert any("robot-at" in m["item"] or "p_robot_elsewhere" in m["item"] for m in sc["user_modified"])


@pytest.mark.parametrize("platform", ["platform_b", "platform_d"])
def test_prior_table_round_trip(platform):
    cfg = E.build_config("large_1", platform)
    ov = E.overrides_from_prior_rows(E.prior_rows(cfg), platform)
    cfg2 = E.build_config("large_1", platform, overrides={"groups": ov})
    assert E.modified_priors(cfg2) == []
    assert E.run(cfg2)["totals"]["offsets"] == pytest.approx(E.run(cfg)["totals"]["offsets"])


def test_prior_table_round_trip_with_robot_elsewhere():
    cfg = E.build_config("large_1", overrides={"groups": {"prostatectomy": {"p_open": 0.2, "p_robot_elsewhere": 0.5}}})
    rows = E.prior_rows(cfg)
    assert any(r["comparator"] == "robot_elsewhere" and r["share"] == 0.5 for r in rows)
    lap = next(r for r in rows if r["group"] == "prostatectomy" and r["comparator"] == "conventional_mis")
    assert lap["share"] == pytest.approx(0.3)
    ov = E.overrides_from_prior_rows(rows, "platform_b")
    assert ov["prostatectomy"]["p_robot_elsewhere"] == 0.5 and ov["prostatectomy"]["p_open"] == 0.2


# ---------------------------------------------------------------------------
# G. Benchmark, sensitivity, register, inputs reload
# ---------------------------------------------------------------------------
def test_benchmark_volume_and_mix():
    cases = BM.benchmark_cases()
    assert sum(cases.values()) == pytest.approx(550)
    uro = sum(cases[k] for k in ("prostatectomy", "nephrectomy", "cystectomy"))
    assert uro / 550 == pytest.approx(43.2 / 89.6)
    r = BM.run_benchmark()
    assert r["cases_per_robot"] == pytest.approx(550)
    assert not any("books" in w for w in r["warnings"])


def test_benchmark_uses_trust_assumptions_and_capital_source():
    trust = E.build_config(overrides={"programme": {"central_capital_per_robot": 1_000_000},
                                      "groups": {"colorectal": {"p_open": 0.4}},
                                      "unit_costs": {"bed_day": 600}})
    b = BM.benchmark_config(trust)
    assert b["programme"]["central_capital_per_robot"] == 1_000_000
    assert b["groups"]["colorectal"]["p_open"] == 0.4 and b["unit_costs"]["bed_day"] == 600
    rows = BM.comparison_rows(E.run(trust), E.run(b))
    assert len(rows) == 9 and all(len(x) == 4 and x[3] for x in rows)


def test_every_benchmark_value_has_a_source():
    src = D.BENCHMARK["sources"]
    assert set(src) >= {"cases_per_robot", "specialty_shares", "within_specialty", "platform"}
    assert "Assumption" in src["cases_per_robot"] and "Assumption" in src["within_specialty"]
    # wording agreed in the v0.5 review: volume category, renormalisation from 90%
    assert "high-volume category" in src["cases_per_robot"] and "performed 500" not in src["cases_per_robot"]
    assert "renormalises" in src["specialty_shares"] and "90%" in src["specialty_shares"]


def test_girft_staffing_wording():
    blocks, _ = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    text = all_text(blocks)
    assert "should be built into the business case" in text
    assert "Required by national guidance" not in text
    regtext = " ".join(r["source"] for r in RG.rows(E.build_config()))
    assert "(requirement)" not in regtext and "required business case item" not in regtext


@pytest.mark.parametrize("metric", list(S.METRICS))
def test_tornado_base_and_ordering(metric):
    cfg = E.build_config("large_2")
    r = E.run(cfg)
    t = S.tornado(cfg, metric, r)
    assert t["base"] == pytest.approx(S.metric_value(r, metric))
    swings = [b["swing"] for b in t["bars"]]
    assert swings == sorted(swings, reverse=True) and swings


def test_tornado_separates_cost_and_clinical_drivers():
    cfg = E.build_config("large_2")
    cost = S.tornado(cfg, "extra_cost")
    assert "Bed-days saved per case" in cost["no_effect"]
    per_bed = S.tornado(cfg, "cost_per_bed_day")
    names = [b["name"] for b in per_bed["bars"]]
    assert "Bed-days saved per case" in names and "Prostatectomy comparator" in names


def test_tornado_one_way_matches_direct_run():
    cfg = E.build_config()
    r = E.run(cfg)
    bar = next(b for b in S.tornado(cfg, "extra_cost", r)["bars"] if b["name"] == "Cost per theatre minute")
    c2 = E.build_config(template=cfg["template"], overrides={"unit_costs": {"theatre_minute": 20}})
    assert bar["high"] == pytest.approx(E.run(c2)["totals"]["extra_cost"])


@pytest.mark.parametrize("preset,platform", [("medium_dgh_1", "platform_b"), ("large_1", "platform_d"),
                                             ("large_2", "platform_c")])
def test_register_complete(preset, platform):
    rows = RG.rows(E.build_config(preset, platform))
    assert rows and all(r["source"] and r["status"] in RG.STATUSES for r in rows)
    assert not any(r["status"] == "Reviewed" for r in rows)


def test_inputs_round_trip_and_errors():
    case = json.load(open(EX / "example_case.json"))
    case["configuration"]["groups"] = {"colorectal": {"volume": 150}}
    case["configuration"]["platform"] = "platform_c"
    case["configuration"]["platform_overrides"] = {"contract_volume_basis": "per_contract"}
    parsed, err = IO.parse_case(json.dumps(case))
    assert err is None
    st = IO.widget_state(parsed)
    assert st["w_platform"] == "platform_c" and st["w_basis"] == "per_contract"
    assert st["w_central"] == 1_000_000 and st["c_trust_name"] == "[Trust name]"
    assert IO.parse_case(b"not json")[1] is not None
    assert IO.parse_case(json.dumps({"cover": {}}))[1] is not None
    bad = dict(case, configuration=dict(case["configuration"], groups={"colorectal": {"p_open": 3}}))
    assert IO.parse_case(json.dumps(bad))[1] is not None


# ---------------------------------------------------------------------------
# H. Business case builder and Word document
# ---------------------------------------------------------------------------
SUPPLIERS = ["da Vinci", "Intuitive", "Versius", "CMR", "Hugo", "Medtronic", "Senhance", "Asensus", " Xi"]


def all_text(blocks):
    out = []
    for b in blocks:
        for k in ("text", "title", "subtitle", "footnote", "caption"):
            if isinstance(b.get(k), str):
                out.append(b[k])
        for k in ("items",):
            out += b.get(k, [])
        if b["type"] == "table":
            out += b["header"]
            for row in b["rows"]:
                out += [str(x) for x in row]
        if b["type"] == "cover":
            out += [f"{a} {c}" for a, c in b["fields"]]
    return "\n".join(out)


@pytest.mark.parametrize("preset", D.PRESETS)
@pytest.mark.parametrize("platform", ["platform_a", "platform_b", "platform_c", "platform_d", "custom_per_procedure"])
def test_business_case_blocks_build(preset, platform):
    case = {"cover": {"trust_name": "Test Trust"},
            "configuration": {"preset": preset, "robots": D.PRESETS[preset]["robots"], "platform": platform,
                              "instrument_price": "standard_discount", "central_capital_per_robot": 1_000_000}}
    blocks, r = BC.build_blocks(case, include_charts=False)
    assert blocks[0]["type"] == "cover" and blocks[0]["trust"] == "Test Trust"
    heads = [b["text"] for b in blocks if b["type"] == "h1"]
    for h in ("1. Executive summary", "2. Strategic case", "3. Economic case", "4. Commercial case",
              "5. Financial case", "6. Management case", "Appendix D. Assumptions register"):
        assert h in heads
    fin = next(b for b in blocks if b["type"] == "table" and b["header"][0] == "£ (thousands)"
               and b["rows"][-1][0] == "Extra cost to the trust")
    assert fin["rows"][-1][-1] == f"{r['totals']['extra_cost'] / 1e3:,.0f}"
    text = all_text(blocks)
    for s in SUPPLIERS:
        assert s not in text, s
    assert not re.search(r"\b[a-z]+_[a-z_]+\b", text), re.findall(r"\b[a-z]+_[a-z_]+\b", text)[:5]
    assert "ROLARR" not in text and "RAPTOR" not in text
    assert "Draft" in dict(blocks[0]["fields"])["Status"]


def test_executive_summary_order():
    blocks, _ = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    h3 = [b["text"] for b in blocks if b["type"] == "h3"]
    i = [h3.index(x) for x in ("What the programme delivers for patients each year (year 3, steady state)",
                               "Cost per outcome (five years)", "Five-year cost to the trust")]
    assert i == sorted(i)


def test_break_even_and_benchmark_in_document():
    blocks, r = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    text = all_text(blocks)
    assert "Break-even:" in text and "3.4 Comparison with a benchmark programme" in text
    assert "3.6 Break-even" in text


def test_word_document_renders_with_draft_header_and_charts():
    from docx import Document
    case = {"cover": {"trust_name": "Test Trust", "prepared_by": "A N Other, Director"},
            "configuration": {"preset": "large_2", "robots": 2, "platform": "platform_b"}}
    data, r = BC.build_docx_bytes(case)
    doc = Document(io.BytesIO(data))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Test Trust" in text and "6. Management case" in text
    assert "DRAFT" in doc.sections[0].header.paragraphs[0].text
    assert len(doc.inline_shapes) == 3


def test_word_document_single_port_renders():
    from docx import Document
    data, _ = BC.build_docx_bytes(json.load(open(EX / "example_case_single_port.json")))
    doc = Document(io.BytesIO(data))
    assert "exploratory" in "\n".join(p.text for p in doc.paragraphs)


# ---------------------------------------------------------------------------
# I. Single-port platform (different maths, same interface)
# ---------------------------------------------------------------------------
def naive_sp_offsets(cfg, r, year):
    uc, pr = cfg["unit_costs"], cfg["programme"]
    m = cfg["evidence_multiplier"] * pr["learning_benefit_by_year"][year - 1]
    u = pr["utilisation_by_year"][year - 1]
    total = 0.0
    for k, g in cfg["groups"].items():
        n = r["groups"][k]["planned_cases"] * u
        for c, sh in g["comparators"].items():
            x = g["reductions"][c]
            total += m * n * sh * (x["los"] * uc["bed_day"] + x["conv"] * uc["conversion"]
                                   + x["reop"] * uc["reoperation"] + x["comp"] * uc["major_complication"]
                                   + x["readm"] * uc["readmission"])
    return total


@pytest.mark.parametrize("preset", D.PRESETS)
@pytest.mark.parametrize("evidence", D.EVIDENCE_SETTINGS)
def test_single_port_independent_offsets(preset, evidence):
    cfg = E.build_config(preset, "platform_d", evidence)
    assert set(cfg["groups"]) == set(D.SP_GROUPS)
    r = E.run(cfg)
    for y in r["yearly"]:
        assert y["offsets"] == pytest.approx(naive_sp_offsets(cfg, r, y["year"]))
    assert r["booked_sessions_per_fortnight"] <= r["capacity_per_fortnight"]


def test_single_port_hand_case():
    # 100 cases: 90 v multi-port (0.5 bed-days each), 10 v open (2 bed-days)
    ev = E.consequences(D.SP_GROUPS["sp_prostatectomy"], 100, 1.0)
    assert ev["bed_days"] == pytest.approx(90 * 0.5 + 10 * 2.0)
    assert ev["open_avoided"] == pytest.approx(10)
    assert ev["extra_minutes"] == pytest.approx(90 * -15)


def test_single_port_shares_must_sum_to_one():
    with pytest.raises(ValueError):
        E.build_config(platform="platform_d",
                       overrides={"groups": {"sp_transanal": {"comparators": {"conventional_mis": 0.5, "open": 0.2}}}})


def test_single_port_exploratory_guardrail():
    g = {x["check"]: x for x in E.run(E.build_config("large_1", "platform_d"))["guardrails"]}
    assert g["Platform evidence base"]["status"] == "amber"


# ---------------------------------------------------------------------------
# J. Two-week theatre template (v0.6)
# ---------------------------------------------------------------------------
def grid_with(cells, robots=1):
    """Build a grid from {(robot, week, day, session): (list type, entry)}."""
    g = T.empty_grid(robots)
    for (rb, w, d, s), (lt, entry) in cells.items():
        row = next(x for x in g[rb - 1] if x["week"] == w and x["day"] == d)
        row[f"{s}_list"], row[f"{s}_cases"] = lt, entry
    return g


def tcfg(grid, demand_check=False, **kw):
    ov = dict(kw.pop("overrides", {}), demand_check=demand_check)
    return E.build_config("large_1", template=grid, overrides=ov, **kw)


HAND = {(1, 1, "Mon", "AM"): ("colorectal", "1 major"),
        (1, 1, "Mon", "PM"): ("colorectal", "Continuing"),
        (1, 1, "Tue", "AM"): ("gynaecology", "2 major"),
        (1, 1, "Tue", "PM"): ("gynaecology", "1 major + 1 minor"),
        (1, 1, "Wed", "AM"): ("", "Closed"),
        (1, 1, "Sat", "AM"): ("urology_prostate", "2 medium")}


def test_case_options():
    o3 = T.case_options(3)
    combos = [x for x in o3 if x not in D.SPECIAL_ENTRIES]
    assert len(combos) == 19 and "1 major + 1 medium + 1 minor" in combos and "3 minor" in combos
    assert all(sum(T.parse_cases(c)[1].values()) <= 3 for c in combos)
    assert len([x for x in T.case_options(4) if x not in D.SPECIAL_ENTRIES]) == 34
    assert T.parse_cases("2 major + 1 minor") == ("combo", {"major": 2, "medium": 0, "minor": 1})
    assert T.parse_cases("two major")[0] == "invalid" and T.parse_cases("Continuing") == ("special", "Continuing")


def test_template_hand_calculation():
    # booked: Mon AM, Mon PM (continuing), Tue AM, Tue PM, Sat AM = 5
    # available: 20 weekday AM/PM - 2 Friday PM maintenance - 1 closed + 1 Saturday booked = 18
    # cases per fortnight (7): colorectal 1; gynaecology majors 3 -> hysterectomy 1.2, endometriosis 1.5,
    # myomectomy 0.3; adnexal 1; prostatectomy 2
    cfg = tcfg(grid_with(HAND))
    ts = T.summarise(cfg)
    assert ts["booked"] == 5 and ts["available"] == 18 and ts["issues"] == []
    c = ts["cases_per_fortnight"]
    for k, v in dict(colorectal=1, hysterectomy=1.2, endometriosis=1.5, myomectomy=0.3, adnexal=1,
                     prostatectomy=2).items():
        assert c[k] == pytest.approx(v)
    r = E.run(cfg)
    assert r["booked_utilisation"] == pytest.approx(5 / 18)
    assert r["groups"]["prostatectomy"]["planned_cases"] == pytest.approx(2 * 22.5)
    assert r["yearly"][2]["cases"] == pytest.approx(7 * 22.5)     # 1 + 3 + 1 + 2 cases per fortnight
    assert r["groups"]["colorectal"]["sessions_per_fortnight"] == pytest.approx(2)   # AM plus continuing


def test_template_evenings_and_weekends_count_only_when_used():
    base = T.summarise(tcfg(T.empty_grid(1)))
    assert base["booked"] == 0 and base["available"] == 18
    g = grid_with({(1, 1, "Mon", "Eve"): ("", "Empty"), (1, 2, "Sun", "PM"): ("colorectal", "1 major")})
    ts = T.summarise(tcfg(g))
    assert ts["available"] == 20 and ts["booked"] == 1


def test_template_validation_messages():
    g = grid_with({(1, 1, "Mon", "AM"): ("colorectal", "Continuing"),
                   (1, 1, "Tue", "AM"): ("", "1 major"),
                   (1, 1, "Wed", "AM"): ("colorectal", ""),
                   (1, 1, "Thu", "AM"): ("gynaecology", "3 major + 1 minor")})
    issues = " ".join(T.summarise(tcfg(g))["issues"])
    assert "'Continuing' must follow a booked session" in issues
    assert "cases entered without a list type" in issues
    assert "list type chosen but no cases" in issues
    assert "exceeds the session maximum of 3" in issues
    r = E.run(tcfg(g))
    assert sum(1 for w in r["warnings"] if w.startswith("Template:")) == 4


def test_max_cases_per_session_is_adjustable():
    g = grid_with({(1, 1, "Thu", "AM"): ("gynaecology", "3 major + 1 minor")})
    assert T.summarise(tcfg(g, overrides={"programme": {"max_cases_per_session": 4}}))["issues"] == []


def test_medium_tier_for_urology_lists():
    for lt, grp in (("urology_prostate", "prostatectomy"), ("urology_kidney", "nephrectomy"),
                    ("urology_bladder", "cystectomy")):
        spec = D.LIST_TYPES[lt]
        assert spec["medium"] == [[grp, 1.0]] and spec["major"] == [] and spec["minor"] == []
    g = grid_with({(1, 1, "Mon", "AM"): ("urology_bladder", "1 medium"),
                   (1, 1, "Mon", "PM"): ("urology_bladder", "Continuing"),
                   (1, 1, "Tue", "AM"): ("urology_prostate", "1 major")})
    r = E.run(tcfg(g))
    assert r["template_summary"]["cases_per_fortnight"]["cystectomy"] == pytest.approx(1)
    assert r["template_summary"]["cases_per_fortnight"]["not_modelled"] == pytest.approx(1)
    assert any("map to no modelled procedure" in w for w in r["warnings"])


def test_not_modelled_cases_cost_but_carry_no_benefit():
    g = grid_with({(1, 1, "Mon", "AM"): ("other", "2 major")})
    r = E.run(tcfg(g))
    y = r["yearly"][2]
    assert y["cases"] == pytest.approx(45) and y["offsets"] == 0 and y["bed_days"] == 0
    assert y["instruments"] == pytest.approx(45 * r["config"]["platform"]["instruments_per_case"])


def test_abdominal_wall_reconstruction_rename_and_flag():
    assert D.PROCEDURE_GROUPS["abdominal_wall"]["label"] == "Abdominal wall reconstruction"
    rows = RG.rows(E.build_config())
    flag = [x for x in rows if x["status"] == "Flagged for review"]
    assert len(flag) == 1 and "ventral and incisional hernia" in flag[0]["source"]
    assert "Flagged for review" in D.EVIDENCE_NOTES["abdominal_wall"]


def test_gynaecology_major_split_and_editable_mapping():
    assert D.LIST_TYPES["gynaecology"]["major"] == [["hysterectomy", 0.40], ["endometriosis", 0.50],
                                                    ["myomectomy", 0.10]]
    g = grid_with({(1, 1, "Tue", "AM"): ("gynaecology", "2 major")})
    cfg = tcfg(g, overrides={"list_map": {"gynaecology": {"major": [["hysterectomy", 1.0]]}}})
    assert T.summarise(cfg)["cases_per_fortnight"]["hysterectomy"] == pytest.approx(2)
    mods = [m for m in E.modified_priors(cfg) if m["item"].startswith("list_map")]
    assert len(mods) == 1 and mods[0]["used"] == "Hysterectomy (benign and malignant) 100%"
    assert E.describe_item(cfg, mods[0]["item"]) == "Template mapping: Gynaecology, major cases"
    assert "endometriosis" in mods[0]["default"].lower()
    assert [m for m in E.modified_priors(E.build_config()) if m["item"].startswith("list_map")] == []


def test_mapping_validation():
    with pytest.raises(ValueError, match="add up to 100%"):
        E.build_config(overrides={"list_map": {"gynaecology": {"major": [["hysterectomy", 0.6]]}}})
    with pytest.raises(ValueError, match="unknown procedure group"):
        E.build_config(overrides={"list_map": {"colorectal": {"minor": [["rectopexy", 1.0]]}}})


def test_mapping_rows_round_trip():
    cfg = E.build_config()
    rebuilt = T.list_map_from_rows(T.mapping_rows(cfg), cfg["list_map"])
    assert rebuilt == cfg["list_map"]
    rows = T.mapping_rows(cfg)
    for row in rows:
        if row["list_type"] == "colorectal" and row["tier"] == "minor":
            row["group"] = "colorectal"
    assert T.list_map_from_rows(rows, cfg["list_map"])["colorectal"]["minor"] == [["colorectal", 1.0]]


def test_demand_check_limits_delivery_and_flags_overscheduling():
    g = grid_with({(1, w, d, s): ("colorectal", "1 major") for w in (1, 2) for d in D.WEEKDAYS
                   for s in ("AM", "PM") if not (d == "Fri" and s == "PM")})
    on = E.run(tcfg(g, demand_check=True, overrides={"groups": {"colorectal": {"volume": 200}}}))
    off = E.run(tcfg(g, demand_check=False, overrides={"groups": {"colorectal": {"volume": 200}}}))
    assert on["groups"]["colorectal"]["template_cases"] == pytest.approx(18 * 22.5)
    assert on["groups"]["colorectal"]["planned_cases"] == pytest.approx(200)
    assert any("only 49% full" in w for w in on["warnings"])
    assert off["groups"]["colorectal"]["planned_cases"] == pytest.approx(405)
    assert off["unmet_cases"] == 0


def test_realisation_factor_scales_templated_cases():
    g = grid_with(HAND)
    a = E.run(tcfg(g))
    b = E.run(tcfg(g, overrides={"programme": {"realisation_factor": 0.8}}))
    assert b["yearly"][2]["cases"] == pytest.approx(0.8 * a["yearly"][2]["cases"])


def test_700_advisory_applies_to_templates():
    g = grid_with({(1, w, d, s): ("gynaecology", "3 minor") for w in (1, 2) for d in D.DAYS for s in D.SESSIONS})
    r = E.run(tcfg(g))
    assert r["yearly"][2]["cases"] == pytest.approx(42 * 3 * 22.5)
    assert any("(advisory)" in w for w in r["warnings"])
    assert next(x for x in r["guardrails"] if x["check"] == "Robotic cases per robot per year")["status"] == "amber"


@pytest.mark.parametrize("preset", D.PRESETS)
@pytest.mark.parametrize("platform", ["platform_b", "platform_d"])
@pytest.mark.parametrize("variant", ["standard", "extended"])
def test_default_templates(preset, platform, variant):
    cfg = E.build_config(preset, platform, template=variant)
    ts = T.summarise(cfg)
    assert ts["issues"] == [] and ts["booked"] > 0 and ts["booked"] <= ts["available"]
    for c in ts["cells"]:
        if c["day"] == "Fri" and c["session"] == "PM":
            assert c["status"] == "maintenance"
        if c["status"] == "booked":
            assert c["list_type"]
        if c["day"] in ("Sat", "Sun"):
            assert c["status"] == "unused"
        if c["session"] == "Eve" and variant == "standard":
            assert c["status"] == "unused"
    evenings = sum(1 for c in ts["cells"] if c["session"] == "Eve" and c["status"] == "booked")
    if variant == "standard":
        assert evenings == 0


def test_extended_variant_uses_evenings_for_large_hospital():
    std = T.summarise(E.build_config("large_1", template="standard"))
    ext = T.summarise(E.build_config("large_1", template="extended"))
    assert ext["booked"] > std["booked"]
    assert any(c["session"] == "Eve" and c["status"] == "booked" for c in ext["cells"])


def test_custom_template_resized_to_robot_count():
    cfg = E.build_config("large_2", template=grid_with(HAND, robots=1))
    assert len(cfg["template"]) == 2 and T.summarise(cfg)["booked"] == 5


def test_options_appraisal_with_custom_template_marks_suggested_option():
    case = {"cover": {}, "configuration": {"preset": "large_1", "robots": 1, "platform": "platform_b",
                                           "template": grid_with(HAND)}}
    blocks, _ = BC.build_blocks(case, include_charts=False)
    text = all_text(blocks)
    assert "Option 2: 2 robots *" in text and "template suggested from demand" in text


def test_business_case_shows_template_and_mapping():
    blocks, r = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    text = all_text(blocks)
    assert "6.1 Two-week theatre template" in text and "Robot 1: two-week template" in text
    assert "How the theatre template maps to procedures" in text
    assert "Gynaecology" in text and "Hysterectomy (benign and malignant) 40%" in text


def test_inputs_round_trip_with_template():
    case = json.load(open(EX / "example_case.json"))
    case["configuration"].update(template=grid_with(HAND), template_variant="custom", demand_check=False,
                                 list_map={"gynaecology": {"major": [["hysterectomy", 1.0]]}},
                                 programme={"max_cases_per_session": 4})
    parsed, err = IO.parse_case(json.dumps(case))
    assert err is None
    st = IO.widget_state(parsed)
    assert st["w_variant"] == "standard" and st["w_maxcases"] == 4 and st["w_demandcheck"] is False
    r = E.run(E.build_config(**BC.configure(parsed)))
    assert r["template_summary"]["booked"] == 5 and r["config"]["list_map"]["gynaecology"]["major"] == [["hysterectomy", 1.0]]


# ---------------------------------------------------------------------------
# K. Tariff (cash case only)
# ---------------------------------------------------------------------------
def test_tariff_defaults_are_zero_and_prostatectomy_is_flagged():
    assert all(g["tariff_uplift"] == 0 for g in D.PROCEDURE_GROUPS.values())
    assert "prostatectomy" in D.TARIFF_SOURCES and "Annex A" in D.TARIFF_SOURCES["prostatectomy"]
    rows = RG.rows(E.build_config("large_1"))
    pro = next(x for x in rows if x["parameter"].startswith("Radical prostatectomy: extra tariff"))
    assert pro["status"] == "Placeholder"


def test_tariff_enters_cash_case_only():
    base = E.run(E.build_config("large_1"))
    cfg = E.build_config("large_1", template=base["config"]["template"],
                         overrides={"groups": {"prostatectomy": {"tariff_uplift": 500.0}}})
    r = E.run(cfg)
    for y0, y in zip(base["yearly"], r["yearly"]):
        pro = y["by_group"]["prostatectomy"]["cases"]
        assert y["tariff_income"] == pytest.approx(500 * pro)
        assert y["net_cash_cost"] == pytest.approx(y["extra_cost"] - y["tariff_income"])
        assert y["extra_cost"] == pytest.approx(y0["extra_cost"])
    assert r["economic"]["net_present_cost"] == pytest.approx(base["economic"]["net_present_cost"])
    assert r["totals"]["cost_per_bed_day_released"] == pytest.approx(base["totals"]["cost_per_bed_day_released"])
    assert r["break_even"]["net_cost_at_plan"] == pytest.approx(base["break_even"]["net_cost_at_plan"])
    assert any(m["item"] == "prostatectomy.tariff_uplift" for m in r["user_modified"])
    assert base["totals"]["tariff_income"] == 0


def test_tariff_in_business_case():
    case = {"cover": {}, "configuration": {"preset": "large_1", "robots": 1, "platform": "platform_b",
                                           "groups": {"prostatectomy": {"tariff_uplift": 500.0}}}}
    blocks, r = BC.build_blocks(case, include_charts=False)
    text = all_text(blocks)
    assert "Less extra tariff income" in text and "Net cash cost to the trust" in text
    assert "only the difference over what the trust would earn" in text
    assert "excluded from the economic view" in text
    blocks0, _ = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    assert "No extra tariff income has been entered" in all_text(blocks0)


def test_tornado_net_cash_metric():
    cfg = E.build_config("large_1", overrides={"groups": {"prostatectomy": {"tariff_uplift": 500.0}}})
    t = S.tornado(cfg, "net_cash")
    assert t["base"] == pytest.approx(E.run(cfg)["totals"]["net_cash_cost"])
    assert any(b["name"] == "Share of templated cases that go ahead" for b in t["bars"])



# ---------------------------------------------------------------------------
# L. v0.6.1: templates fill until demand is met, blanks, advisory cap, cancellations
# ---------------------------------------------------------------------------
TEMPLATE_CASES = list(itertools.product(D.PRESETS, ["platform_b", "platform_d"], ["standard", "extended"]))


def open_standard_sessions(ts):
    return [c for c in ts["cells"] if c["status"] == "open"]


@pytest.mark.parametrize("preset,platform,variant", TEMPLATE_CASES)
def test_default_templates_fill_until_demand_met_or_sessions_run_out(preset, platform, variant):
    # v0.6.0 left 4 medium DGH sessions unbooked while 85 cases a year went unscheduled
    r = E.run(E.build_config(preset, platform, template=variant))
    ts = r["template_summary"]
    if open_standard_sessions(ts):
        assert r["unmet_cases"] < 0.5, (preset, platform, variant, r["unmet_cases"])


@pytest.mark.parametrize("preset,platform,variant", TEMPLATE_CASES)
def test_extended_day_uses_evenings_only_when_daytime_is_full(preset, platform, variant):
    ts = E.run(E.build_config(preset, platform, template=variant))["template_summary"]
    for rb in {c["robot"] for c in ts["cells"]}:
        cells = [c for c in ts["cells"] if c["robot"] == rb]
        if any(c["session"] == "Eve" and c["status"] == "booked" for c in cells):
            assert not [c for c in cells if c["status"] == "open"]


@pytest.mark.parametrize("preset", D.PRESETS)
def test_filler_trims_last_session_to_cases_needed(preset):
    # for procedures that are the only procedure in their tier, the template overshoots
    # demand by less than one case per fortnight (22.5 a year)
    cfg = E.build_config(preset, overrides={"demand_check": False})
    ts = T.summarise(cfg)
    solo = {g for spec in cfg["list_map"].values() for t in D.TIERS for g, _ in spec[t] if len(spec[t]) == 1}
    multi = {g for spec in cfg["list_map"].values() for t in D.TIERS for g, _ in spec[t] if len(spec[t]) > 1}
    for g in solo - multi:
        tc = ts["cases_per_fortnight"][g] * 22.5
        assert tc < cfg["groups"][g]["volume"] + 22.5 + 1e-6, g


def test_suggest_from_demand_meets_extra_demand_with_spare_sessions():
    cfg = E.build_config("medium_dgh_2", template=None, overrides={"groups": {"upper_gi": {"volume": 60}}})
    r = E.run(E.build_config("medium_dgh_2", template=T.suggest_template(cfg),
                             overrides={"groups": {"upper_gi": {"volume": 60}}}))
    assert r["groups"]["upper_gi"]["unmet_cases"] < 0.5 and r["unmet_cases"] < 0.5


def test_suggest_from_demand_allows_for_cancellations():
    base = E.build_config("medium_dgh_2", template=None)
    low = E.build_config("medium_dgh_2", template=None, overrides={"programme": {"realisation_factor": 0.8}})
    assert T.summarise(base, T.suggest_template(low))["booked"] > T.summarise(base, T.suggest_template(base))["booked"]
    r = E.run(E.build_config("medium_dgh_2", template=T.suggest_template(low),
                             overrides={"programme": {"realisation_factor": 0.8}}))
    assert r["unmet_cases"] < 0.5


def test_v05_demand_volumes_restored():
    v = {k: (g["cases_medium"], g["cases_large"]) for k, g in D.PROCEDURE_GROUPS.items()}
    assert v["hysterectomy"] == (100, 160) and v["myomectomy"] == (25, 40) and v["endometriosis"] == (40, 60)
    assert D.BENCHMARK["within_specialty"]["Gynaecology"] == {"hysterectomy": 0.60, "endometriosis": 0.20,
                                                              "myomectomy": 0.10, "adnexal": 0.10}


def test_split_mismatch_is_explained():
    r = E.run(E.build_config("medium_dgh_1"))
    w = [x for x in r["warnings"] if x.startswith("Gynaecology major cases: the template split")]
    assert len(w) == 1 and "hysterectomy 40%" in w[0] and "hysterectomy 61%" in w[0]
    consistent = {"hysterectomy": {"volume": 66}, "endometriosis": {"volume": 83}, "myomectomy": {"volume": 16}}
    r2 = E.run(E.build_config("medium_dgh_1", overrides={"groups": consistent}))
    assert not any("template split" in x for x in r2["warnings"])


def test_cancellation_factor_scales_delivery():
    # with the demand check off, delivery scales exactly; with it on, procedures scheduled
    # above demand are unaffected until the factor brings them below it
    base = E.build_config("large_1")
    off = {"demand_check": False}
    a = E.run(E.build_config("large_1", template=base["template"], overrides=off))
    b = E.run(E.build_config("large_1", template=base["template"],
                             overrides=dict(off, programme={"realisation_factor": 0.9})))
    assert b["yearly"][2]["cases"] == pytest.approx(0.9 * a["yearly"][2]["cases"])
    on_a = E.run(base)
    on_b = E.run(E.build_config("large_1", template=base["template"], overrides={"programme": {"realisation_factor": 0.9}}))
    for k, g in on_b["groups"].items():
        # template_cases already includes the 0.9 factor
        assert g["template_cases"] == pytest.approx(0.9 * on_a["groups"][k]["template_cases"])
        assert g["planned_cases"] == pytest.approx(min(g["template_cases"], g["ceiling"])
                                                   if k not in D.NOT_MODELLED else g["template_cases"])
    assert on_b["yearly"][2]["cases"] <= on_a["yearly"][2]["cases"]
    assert D.PROGRAMME["realisation_factor"] == 1.0


def test_ui_rows_show_blanks_not_none_and_round_trip():
    cfg = E.build_config("medium_dgh_1")
    labels = {k: v["label"] for k, v in cfg["list_map"].items()}
    rows = T.to_ui_rows(cfg["template"][0], labels)
    for row in rows:
        for k, v in row.items():
            assert v is not None and v != "" and v != "None", (k, v)
    assert rows[0]["Evening cases"] == T.BLANK and T.BLANK.strip() == ""
    back = T.from_ui_rows(rows, {v: k for k, v in labels.items()})
    assert back == cfg["template"][0]
    odd = dict(rows[0], **{"AM list": None, "AM cases": float("nan")})
    assert T.from_ui_rows([odd], {})[0]["AM_cases"] == "" and T.from_ui_rows([odd], {})[0]["AM_list"] == ""
    assert T.BLANK in T.ui_options(T.case_options(3)) and "" not in T.ui_options(T.case_options(3))


def test_inputs_round_trip_cancellation_factor():
    case = json.load(open(EX / "example_case.json"))
    case["configuration"]["programme"] = {"realisation_factor": 0.85}
    parsed, err = IO.parse_case(json.dumps(case))
    assert err is None and IO.widget_state(parsed)["w_realisation"] == 85
