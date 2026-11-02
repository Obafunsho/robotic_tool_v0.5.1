"""
Tests for the robotic programme decision engine (v0.8).

Layers:
  A. Hand-calculated toy operation on a rota (every number worked out on paper).
  B. Invariants across presets, platforms and evidence settings.
  C. Independent cross-check of cost avoided and rota operations.
  D. Rota input: sessions available, operations, "cont.", validation, examples, web conversion.
  E. Clinical lead's literature review applied as defaults.
  F. Removals and simplifications (demand, single-port, complexity, hospital type).
  G. Existing robots, unit costs and advanced inputs.
  H. Break-even, price targets, platforms, contracts, capital, cap, cancellations.
  I. Benchmark, sensitivity and assumptions register (Excel).
  J. Business case builder and Word document.
"""
import io
import itertools
import json
import re
from pathlib import Path

import pytest

import benchmark as BM
import business_case as BC
import defaults as D
import engine as E
import evidence_review as ER
import register as RG
import register_xlsx as RX
import sensitivity as S
import templates as T

EX = Path(__file__).parent / "examples"
PLATFORMS = list(D.PLATFORMS)
ALL = list(itertools.product(D.PRESETS, PLATFORMS, D.EVIDENCE_SETTINGS))


def rota(entries, sessions=None, robots=1):
    """Build a rota. entries: {(robot, week, day, session): (procedure, operations)};
    sessions: {(robot, week, day): n} (others keep the default: weekdays 2, weekends 0)."""
    g = T.empty_grid(robots)
    for (rb, w, d), n in (sessions or {}).items():
        next(x for x in g[rb - 1] if x["week"] == w and x["day"] == d)["sessions"] = n
    for (rb, w, d, s), (p, c) in entries.items():
        row = next(x for x in g[rb - 1] if x["week"] == w and x["day"] == d)
        row[f"{s}_proc"], row[f"{s}_cases"] = p, str(c)
    return g


# ---------------------------------------------------------------------------
# A. Hand-calculated toy case
# ---------------------------------------------------------------------------
TOY_SESSIONS = {(1, w, d): (2 if d in ("Mon", "Tue") else 0) for w in (1, 2) for d in D.DAYS}
TOY_ROTA = rota({(1, 1, "Mon", "AM"): ("colectomy", 4), (1, 1, "Mon", "PM"): ("colectomy", 1)}, TOY_SESSIONS)


def toy_cfg(**prog):
    """One robot, colectomy only: 5 operations a fortnight x 20 fortnights = 100 operations a year.
    8 sessions available (Mon and Tue, both weeks), 2 booked."""
    groups = dict(colectomy=dict(
        p_open=0.5, los_reduction_open=2, los_reduction_lap=1, conv_reduction_lap=0.1,
        reop_reduction_open=0.1, reop_reduction_lap=0, comp_reduction_open=0.1, comp_reduction_lap=0,
        readm_reduction_open=0.1, readm_reduction_lap=0, extra_minutes_open=10, extra_minutes_lap=10))
    programme = dict(operating_weeks_per_year=40, utilisation_by_year=[1] * 5, learning_benefit_by_year=[1] * 5,
                     implementation_cost_per_robot=0, theatre_modification_per_robot=0, sfa_wte_per_robot=0,
                     pdc_rate=0.0, discount_rate=0.10, horizon_years=5)
    programme.update(prog)
    return E.build_config(
        preset="medium_dgh_1", platform="platform_b", evidence="central", template=TOY_ROTA,
        overrides=dict(groups=groups, programme=programme,
                       unit_costs=dict(bed_day=100, reoperation=1000, major_complication=1000, readmission=1000,
                                       conversion=1000, theatre_minute=10, decontamination_per_case=0),
                       platform=dict(capital=1_000_000, trade_in=0, asset_life_years=5,
                                     maintenance_per_year=100_000, instruments_per_case=1000)))


def test_toy_rota_and_cases():
    r = E.run(toy_cfg())
    assert r["template_summary"]["booked"] == 2 and r["template_summary"]["available"] == 8
    assert r["booked_utilisation"] == pytest.approx(0.25)
    assert r["groups"]["colectomy"]["planned_cases"] == pytest.approx(100)
    y = r["yearly"][0]
    assert y["open_avoided"] == pytest.approx(50) and y["lap_displaced"] == pytest.approx(50)


def test_toy_consequences():
    y = E.run(toy_cfg())["yearly"][0]
    assert y["bed_days"] == pytest.approx(50 * 2 + 50 * 1)
    assert y["conversions"] == pytest.approx(5)
    assert y["reoperations"] == pytest.approx(5) and y["complications"] == pytest.approx(5)
    assert y["readmissions"] == pytest.approx(5)


def test_toy_costs():
    y = E.run(toy_cfg())["yearly"][0]
    assert y["offsets"] == pytest.approx(150 * 100 + 4 * 5 * 1000)       # 35,000
    assert y["theatre_time_cost"] == pytest.approx(100 * 10 * 10)        # 10,000
    assert y["instruments"] == pytest.approx(100 * 1000)
    assert y["platform_fixed"] == pytest.approx(200_000 + 100_000)
    assert y["extra_cost"] == pytest.approx(410_000)
    assert y["net_cost"] == pytest.approx(375_000)


def test_toy_five_year_and_ratios():
    t = E.run(toy_cfg())["totals"]
    assert t["extra_cost"] == pytest.approx(5 * 410_000)
    assert t["cost_per_open_operation_avoided"] == pytest.approx(2_050_000 / 250)
    assert t["cost_per_bed_day_released"] == pytest.approx(2_050_000 / 750)
    assert t["net_cost_per_bed_day_released"] == pytest.approx(1_875_000 / 750)


def test_toy_economic_npc():
    e = E.run(toy_cfg())["economic"]
    annuity = sum(1 / 1.1 ** t for t in range(1, 6))
    assert e["net_present_cost"] == pytest.approx(1_000_000 + 175_000 * annuity)
    e0 = E.run(toy_cfg(discount_rate=0.0))["economic"]
    assert e0["net_present_cost"] == pytest.approx(1_000_000 + 5 * 175_000)


def test_toy_pdc():
    cfg = toy_cfg(pdc_rate=0.035)
    assert E.platform_cost_year(cfg, 1, 100)["detail"]["pdc"] == pytest.approx(31_500)
    assert E.platform_cost_year(cfg, 3, 100)["detail"]["pdc"] == pytest.approx(0.035 * 500_000)


def test_toy_new_cost_lines():
    cfg = toy_cfg(sfa_wte_per_robot=1.5, sfa_cost_per_wte=40_000, theatre_modification_per_robot=30_000)
    cfg["unit_costs"]["decontamination_per_case"] = 50
    y1, y2 = E.run(cfg)["yearly"][:2]
    assert y1["decontamination"] == pytest.approx(5_000) and y1["staffing"] == pytest.approx(60_000)
    assert y1["theatre_modification"] == pytest.approx(30_000) and y2["theatre_modification"] == 0
    assert y1["extra_cost"] == pytest.approx(410_000 + 95_000) and y2["extra_cost"] == pytest.approx(475_000)


def test_toy_break_even_within_and_beyond_capacity():
    # bed-day 2,000: cost avoided per case 3,200; variable 1,100; margin 2,100; fixed 300,000 ->
    # 142.857 cases, within the maximum of 400 (100 cases on 2 of 8 available sessions)
    cfg = toy_cfg()
    cfg["unit_costs"]["bed_day"] = 2000
    be = E.run(cfg)["break_even"]
    assert be["status"] == "within_capacity" and be["max_cases"] == pytest.approx(400)
    assert be["break_even_cases"] == pytest.approx(300_000 / 2_100, rel=1e-6)
    # bed-day 1,000: margin 600 -> 500 cases, beyond the 400 the sessions allow
    cfg["unit_costs"]["bed_day"] = 1000
    be = E.run(cfg)["break_even"]
    assert be["status"] == "beyond_capacity" and be["break_even_cases"] is None
    assert be["net_cost_at_max"] == pytest.approx(300_000 - 400 * 600)
    be = E.run(toy_cfg())["break_even"]
    assert be["status"] == "none" and be["marginal_net_cost_per_extra_case"] == pytest.approx(750)


# ---------------------------------------------------------------------------
# B. Invariants
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("preset,platform,evidence", ALL)
def test_invariants(preset, platform, evidence):
    r = E.run(E.build_config(preset, platform, evidence))
    ts = r["template_summary"]
    assert ts["issues"] == [] and 0 < ts["booked"] <= ts["available"]
    assert r["booked_utilisation"] == pytest.approx(ts["booked"] / ts["available"])
    for y in r["yearly"]:
        parts = (y["platform_fixed"] + y["instruments"] + y["decontamination"] + y["staffing"]
                 + y["theatre_time_cost"] + y["implementation"] + y["theatre_modification"])
        assert y["extra_cost"] == pytest.approx(parts)
        assert y["net_cost"] == pytest.approx(y["extra_cost"] - y["offsets"])
    if evidence == "no_benefit":
        assert all(y["offsets"] == 0 for y in r["yearly"])


@pytest.mark.parametrize("preset", D.PRESETS)
def test_offsets_scale_with_evidence_but_cost_does_not(preset):
    cons = E.run(E.build_config(preset, evidence="conservative"))
    cent = E.run(E.build_config(preset, evidence="central"))
    assert cent["totals"]["offsets"] == pytest.approx(2 * cons["totals"]["offsets"])
    assert cent["totals"]["extra_cost"] == pytest.approx(cons["totals"]["extra_cost"])


def test_consequences_linear_in_cases():
    g = D.PROCEDURE_GROUPS["colectomy"]
    a, b = E.consequences(g, 100, 1.0), E.consequences(g, 200, 1.0)
    for k in E.EVENT_KEYS:
        assert b[k] == pytest.approx(2 * a[k])


def test_empty_rota_leaves_only_fixed_costs():
    r = E.run(E.build_config(template=None))
    y = r["yearly"][2]
    assert y["cases"] == 0 and y["offsets"] == 0 and y["instruments"] == 0
    assert y["extra_cost"] == pytest.approx(y["platform_fixed"] + y["staffing"])
    assert r["break_even"]["status"] == "no_cases" and r["booked_utilisation"] == 0


def test_validation_rejects_bad_inputs():
    for ov in ({"groups": {"colectomy": {"p_open": 1.2}}}, {"groups": {"colectomy": {"los_reduction_open": -1}}},
               {"groups": {"colectomy": {"complexity": "Very high"}}}, {"unit_costs": {"bed_day": -5}},
               {"programme": {"realisation_factor": 0}}, {"existing_robots": "7"},
               {"platform": {"contract_volume_basis": "per_site"}}):
        with pytest.raises(ValueError):
            E.build_config(overrides=ov)


def test_capacity_value_toggle():
    off = E.run(E.build_config())
    on = E.run(E.build_config(overrides={"programme": {"include_capacity_value": True}}))
    y = on["yearly"][2]
    assert y["capacity_value"] == pytest.approx(y["extra_elective_cases_enabled"] * 1500)
    assert off["yearly"][2]["net_cost"] - y["net_cost"] == pytest.approx(y["capacity_value"])


def test_guardrails_present_and_valid():
    g = E.run(E.build_config())["guardrails"]
    assert [x["check"] for x in g] == [
        "Robotic operations per robot per year", "Procedures with 30-day benefit not yet modelled",
        "Robot utilisation (sessions booked / available)", "Share of robotic operations displacing open surgery (advisory)",
        "Instrument price basis", "Platform price", "Assumptions changed from defaults"]
    assert all(x["status"] in ("green", "amber", "red") for x in g)


# ---------------------------------------------------------------------------
# C. Independent cross-checks
# ---------------------------------------------------------------------------
def naive_offsets(cfg, r, year):
    uc, pr = cfg["unit_costs"], cfg["programme"]
    m = cfg["evidence_multiplier"] * pr["learning_benefit_by_year"][year - 1]
    u = pr["utilisation_by_year"][year - 1]
    total = 0.0
    for k, g in cfg["groups"].items():
        n = r["groups"][k]["planned_cases"] * u
        o, l = n * g["p_open"], n * (1 - g["p_open"] - g.get("p_robot_elsewhere", 0))
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


@pytest.mark.parametrize("preset", D.PRESETS)
def test_independent_rota_cases(preset):
    cfg = E.build_config(preset)
    counts = {k: 0 for k in cfg["groups"]}
    for robot in cfg["template"]:
        for row in robot:
            for s in D.SESSIONS[:row["sessions"]]:
                c = row[f"{s}_cases"]
                if row[f"{s}_proc"] and c.isdigit():
                    counts[row[f"{s}_proc"]] += int(c)
    r = E.run(cfg)
    for k in cfg["groups"]:
        assert r["groups"][k]["planned_cases"] == pytest.approx(counts[k] * 22.5)


# ---------------------------------------------------------------------------
# D. Rota input
# ---------------------------------------------------------------------------
def tcfg(grid, **kw):
    return E.build_config("large_1", template=grid, **kw)


def test_sessions_available_options_and_defaults():
    assert D.SESSIONS_AVAILABLE_OPTIONS == [0, 2, 3]
    row = T.empty_robot()
    assert {r["day"]: r["sessions"] for r in row if r["week"] == 1} == {
        "Mon": 2, "Tue": 2, "Wed": 2, "Thu": 2, "Fri": 2, "Sat": 0, "Sun": 0}
    ts = T.summarise(tcfg(T.empty_grid(1)))
    assert ts["available"] == 20 and ts["booked"] == 0


def test_rota_hand_calculation_with_three_sessions_and_cont():
    # Mon wk1 3 sessions: rectal 1, rectal cont., inguinal 2 (Aneel's example row)
    # Tue wk1: cystectomy 1, cont. ; Sat wk2 set to 2 sessions: prostatectomy 2 in session 1
    g = rota({(1, 1, "Mon", "AM"): ("rectal", 1), (1, 1, "Mon", "PM"): ("rectal", D.CONT),
              (1, 1, "Mon", "Eve"): ("inguinal", 2), (1, 1, "Tue", "AM"): ("cystectomy", 1),
              (1, 1, "Tue", "PM"): ("cystectomy", D.CONT), (1, 2, "Sat", "AM"): ("prostatectomy", 2)},
             {(1, 1, "Mon"): 3, (1, 2, "Sat"): 2})
    ts = T.summarise(tcfg(g))
    assert ts["issues"] == []
    assert ts["available"] == 20 + 1 + 2 and ts["booked"] == 6
    c = ts["cases_per_fortnight"]
    assert (c["rectal"], c["inguinal"], c["cystectomy"], c["prostatectomy"]) == (1, 2, 1, 2)
    r = E.run(tcfg(g))
    assert r["booked_utilisation"] == pytest.approx(6 / 23)
    assert r["yearly"][2]["cases"] == pytest.approx(6 * 22.5)
    assert r["groups"]["rectal"]["sessions_per_fortnight"] == 2


def test_cont_can_span_three_sessions_but_not_four_or_switch_procedure():
    ok = rota({(1, 1, "Mon", "AM"): ("whipple", 1), (1, 1, "Mon", "PM"): ("whipple", D.CONT),
               (1, 1, "Mon", "Eve"): ("whipple", D.CONT)}, {(1, 1, "Mon"): 3})
    assert T.summarise(tcfg(ok))["issues"] == []
    bad = rota({(1, 1, "Mon", "AM"): ("liver", D.CONT), (1, 1, "Tue", "AM"): ("rectal", 1),
                (1, 1, "Tue", "PM"): ("colectomy", D.CONT)})
    issues = T.summarise(tcfg(bad))["issues"]
    assert len(issues) == 2 and all("'cont.' must follow" in i for i in issues)


def test_rota_validation_messages():
    g = rota({(1, 1, "Mon", "Eve"): ("colectomy", 1), (1, 1, "Tue", "AM"): ("", 2),
              (1, 1, "Wed", "AM"): ("colectomy", ""), (1, 1, "Thu", "AM"): ("rectopexy", 1),
              (1, 1, "Sat", "AM"): ("colectomy", 1)})
    g[0][4]["sessions"] = 1
    text = " ".join(T.summarise(tcfg(g))["issues"])
    assert "not available on this day" in text
    assert "operations entered without a procedure" in text
    assert "no operations entered" in text
    assert "is not a listed procedure" in text
    assert "sessions available must be 0, 2 or 3" in text
    r = E.run(tcfg(g))
    assert sum(1 for w in r["warnings"] if w.startswith("Rota:")) == 6


def test_case_options_and_no_maintenance_option():
    assert D.CASE_OPTIONS == ["1", "2", "3", "4", "cont."]
    cfg = E.build_config()
    opts = T.procedure_options(cfg)
    assert opts[0] == "Unfilled session" and len(opts) == 18
    assert "Maintenance" not in opts and "Closed" not in opts
    assert "Rectal resection (anterior resection, APR)" in opts and T.case_options()[0] == T.BLANK_CASES


@pytest.mark.parametrize("preset", D.PRESETS)
def test_example_rotas_valid(preset):
    cfg = E.build_config(preset)
    ts = T.summarise(cfg)
    assert ts["issues"] == [] and len(cfg["template"]) == D.PRESETS[preset]["robots"]
    for robot in cfg["template"]:
        for row in robot:
            assert row["sessions"] == (0 if row["day"] in ("Sat", "Sun") else 2)
    booked_per_robot = {rb: sum(1 for c in ts["cells"] if c["robot"] == rb and c["status"] == "booked")
                        for rb in range(1, cfg["robots"] + 1)}
    assert all(v > 0 for v in booked_per_robot.values())     # robot 2 is pre-filled too


def test_ui_rows_round_trip():
    cfg = E.build_config("large_2")
    for robot in cfg["template"]:
        rows = T.to_ui_rows(cfg, robot)
        assert list(rows[0]) == T.ui_columns()
        assert all(v not in ("", None, "None") for row in rows for v in row.values())
        assert T.from_ui_rows(cfg, rows) == robot
    rows = T.to_ui_rows(cfg, cfg["template"][0])
    odd = dict(rows[0], **{"Session 1 (AM): procedure": None, "Session 1 operations": float("nan")})
    back = T.from_ui_rows(cfg, [odd])[0]
    assert back["AM_proc"] == "" and back["AM_cases"] == ""


# ---------------------------------------------------------------------------
# E. Clinical lead's literature review applied as defaults
# ---------------------------------------------------------------------------
def test_review_changes_match_defaults():
    changed = {k: e for k, e in ER.REVIEW.items() if abs(e["value"] - e["v07"]) > 1e-12}
    assert len(changed) == 20
    for id_, e in ER.REVIEW.items():
        k, f = id_.split(".")
        got = D.PROCEDURE_GROUPS[k][f]
        if id_ in changed:
            assert got == pytest.approx(e["value"]), id_
        else:
            assert abs(got - e["v07"]) < 5e-3, id_      # register showed values rounded to 0.1 or 1 percent


def test_length_of_stay_and_open_share_increases_not_applied():
    P = D.PROCEDURE_GROUPS
    assert set(ER.EXCLUDED_INCREASES) == {
        "abdo_wall_repair.los_reduction_open", "benign_gyn.p_open", "benign_gyn.los_reduction_open",
        "gyn_oncology.p_open", "gyn_oncology.los_reduction_open", "rectal.los_reduction_lap",
        "prostatectomy.los_reduction_open"}
    assert P["abdo_wall_repair"]["los_reduction_open"] == 1.5
    assert P["benign_gyn"]["p_open"] == pytest.approx(0.4667) and P["benign_gyn"]["los_reduction_open"] == 1.5
    assert P["gyn_oncology"]["p_open"] == 0.5 and P["gyn_oncology"]["los_reduction_open"] == 1.5
    assert P["rectal"]["los_reduction_lap"] == 0.5 and P["prostatectomy"]["los_reduction_open"] == 2.0
    for i in ER.EXCLUDED_INCREASES:
        assert ER.REVIEW[i]["status"] == "Clinical lead input" and "kept the v0.7 value" in ER.REVIEW[i]["source"]


def test_complication_and_reoperation_increases_applied():
    P = D.PROCEDURE_GROUPS
    assert P["colectomy"]["comp_reduction_lap"] == 0.01 and P["abdo_wall_repair"]["comp_reduction_open"] == 0.04
    assert P["gyn_oncology"]["conv_reduction_lap"] == 0.04 and P["gyn_oncology"]["comp_reduction_open"] == 0.04
    assert P["rectal"]["comp_reduction_lap"] == 0.01 and P["rectal"]["reop_reduction_lap"] == 0.01


def test_benefit_reductions_theatre_time_and_cystectomy_applied():
    P = D.PROCEDURE_GROUPS
    assert P["abdo_wall_repair"]["los_reduction_lap"] == 0 and P["abdo_wall_repair"]["extra_minutes_lap"] == 60
    assert P["benign_gyn"]["conv_reduction_lap"] == 0.01 and P["benign_gyn"]["extra_minutes_lap"] == 40
    assert P["colectomy"]["extra_minutes_lap"] == 40 and P["inguinal"]["extra_minutes_lap"] == 18
    assert P["cystectomy"]["los_reduction_open"] == 1.0 and P["cystectomy"]["readm_reduction_open"] == 0.07


def test_cholecystectomy_neutral_with_extra_minutes():
    g = D.PROCEDURE_GROUPS["cholecystectomy"]
    assert g["benefit_status"] == "neutral" and g["benefit_modelled"] is True
    assert all(g[f] == 0 for f in D.BENEFIT_KEYS) and g["extra_minutes_lap"] == 12
    rows = {r["id"]: r for r in RX.register_rows()}
    for f in ("los_reduction_lap", "conv_reduction_lap", "comp_reduction_lap"):
        assert rows[f"cholecystectomy.{f}"]["status"] == "Neutral (clinical lead)"
    r = E.run(E.build_config())
    assert not any("Complex cholecystectomy" in w and "not yet modelled" in w for w in r["warnings"])


def test_review_citations_carried_into_register():
    rows = {r["id"]: r for r in RX.register_rows()}
    assert "Catto et al" in rows["cystectomy.los_reduction_open"]["source"]
    assert rows["cystectomy.los_reduction_open"]["grade"] == "Randomised trial"
    assert rows["benign_gyn.comp_reduction_lap"]["grade"] == "Cochrane systematic review"
    assert rows["colectomy.p_open"]["status"] == "Needs evidence"
    assert rows["breast.los_reduction_open"]["status"] == "Not yet modelled"


def test_gynaecology_benefit_kept_and_lacc_note():
    assert D.PROCEDURE_GROUPS["gyn_oncology"]["benefit_status"] == "modelled"
    assert "LACC" in D.EVIDENCE_NOTES["gyn_oncology"]
    blocks, _ = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    assert "LACC trial" in all_text(blocks) and "about 90% of hysterectomies are benign" in all_text(blocks)


def test_prostatectomy_tariff_uplift_default_3000():
    g = D.PROCEDURE_GROUPS["prostatectomy"]
    assert g["tariff_uplift"] == 3000.0
    assert all(v["tariff_uplift"] == 0 for k, v in D.PROCEDURE_GROUPS.items() if k != "prostatectomy")
    assert "LB69Z" in D.TARIFF_SOURCES["prostatectomy"] and "averaged to £3,000" in D.TARIFF_SOURCES["prostatectomy"]
    # cash case only: income = 3,000 x prostatectomy cases; economic view and cost per outcome unchanged
    r = E.run(E.build_config("large_1"))
    zero = E.run(E.build_config("large_1", overrides={"groups": {"prostatectomy": {"tariff_uplift": 0.0}}}))
    for y in r["yearly"]:
        assert y["tariff_income"] == pytest.approx(3000 * y["by_group"]["prostatectomy"]["cases"])
        assert y["net_cash_cost"] == pytest.approx(y["extra_cost"] - y["tariff_income"])
    assert r["economic"]["net_present_cost"] == pytest.approx(zero["economic"]["net_present_cost"])
    assert r["totals"]["cost_per_bed_day_released"] == pytest.approx(zero["totals"]["cost_per_bed_day_released"])
    assert not any(m["item"] == "prostatectomy.tariff_uplift" for m in r["user_modified"])
    row = next(x for x in RX.register_rows() if x["id"] == "prostatectomy.tariff_uplift")
    assert row["raw"] == 3000.0 and row["grade"] == "Clinical lead input" and row["status"] == "Clinical lead input"
    assert row["assumption"].startswith("Tariff uplift (difference over existing tariff)")
    text = all_text(BC.build_blocks({"cover": {}, "configuration": {"preset": "large_1", "robots": 1,
                                                                     "platform": "platform_b"}},
                                    include_charts=False)[0])
    assert "Less tariff uplift (difference over existing tariff)" in text
    assert "default tariff uplift of £3,000 per operation" in text
    assert "Extra income per operation" not in text and "extra tariff income" not in text.lower()


# ---------------------------------------------------------------------------
# F. Removals and simplifications
# ---------------------------------------------------------------------------
def test_no_demand_single_port_or_case_counts_from_complexity():
    assert "platform_d" not in D.PLATFORMS and not hasattr(D, "SP_GROUPS")
    for g in D.PROCEDURE_GROUPS.values():
        for f in ("cases_medium", "cases_large", "cases_per_session", "whole_day", "volume"):
            assert f not in g
    assert not hasattr(E, "auto_plan") and not hasattr(T, "suggest_template")


def test_complexity_is_descriptive_only():
    base = E.run(E.build_config())
    changed = E.run(E.build_config(overrides={"groups": {k: {"complexity": "Low"} for k in D.PROCEDURE_GROUPS}}))
    assert changed["yearly"][2]["cases"] == pytest.approx(base["yearly"][2]["cases"])
    assert changed["totals"]["extra_cost"] == pytest.approx(base["totals"]["extra_cost"])


def test_maths_does_not_depend_on_hospital_type():
    g = E.build_config("large_1")["template"]
    a = E.run(E.build_config("medium_dgh_1", template=g))
    b = E.run(E.build_config("large_1", template=g))
    for key in ("extra_cost", "offsets", "bed_days", "cases", "net_present_cost"):
        va = a["economic"]["net_present_cost"] if key == "net_present_cost" else a["totals"][key]
        vb = b["economic"]["net_present_cost"] if key == "net_present_cost" else b["totals"][key]
        assert va == pytest.approx(vb), key
    assert a["break_even"] == b["break_even"]


# ---------------------------------------------------------------------------
# G. Existing robots, unit costs and advanced inputs
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("n", D.EXISTING_ROBOT_OPTIONS)
def test_existing_robots_stated_but_not_in_maths(n):
    case = {"cover": {}, "configuration": {"preset": "medium_dgh_1", "robots": 1, "platform": "platform_b",
                                           "existing_robots": n}}
    blocks, r = BC.build_blocks(case, include_charts=False)
    assert D.existing_robots_text(n) in all_text(blocks)
    assert "robot(s)" not in all_text(blocks)
    base = E.run(E.build_config())
    assert r["totals"]["extra_cost"] == pytest.approx(base["totals"]["extra_cost"])


def test_unit_costs_editable_and_flagged():
    cfg = E.build_config(overrides={"unit_costs": {"bed_day": 600, "theatre_minute": 20,
                                                   "decontamination_per_case": 100},
                                    "programme": {"sfa_cost_per_wte": 70_000}})
    r, base = E.run(cfg), E.run(E.build_config())
    items = {m["item"] for m in r["user_modified"]}
    assert {"unit_costs.bed_day", "unit_costs.theatre_minute", "unit_costs.decontamination_per_case",
            "programme.sfa_cost_per_wte"} <= items
    assert E.describe_item(cfg, "programme.sfa_cost_per_wte") == "Surgical first assistant: cost per WTE"
    assert r["totals"]["extra_cost"] > base["totals"]["extra_cost"]
    assert r["totals"]["offsets"] > base["totals"]["offsets"]


def test_prior_table_round_trip():
    cfg = E.build_config()
    ov = E.overrides_from_prior_rows(E.prior_rows(cfg))
    assert E.modified_priors(E.build_config(overrides={"groups": ov})) == []


def test_prostatectomy_scenario_cuts_benefits_not_costs():
    base = E.run(E.build_config("large_1"))
    sc = E.run(E.build_config("large_1", overrides={"groups": BC.PROSTATE_ELSEWHERE}))
    assert sc["totals"]["bed_days"] < base["totals"]["bed_days"]
    assert sc["totals"]["extra_cost"] == pytest.approx(base["totals"]["extra_cost"])


# ---------------------------------------------------------------------------
# H. Platforms, contracts, capital, cap, cancellations, price targets
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("inject", [1_000_000, 2_000_000])
def test_central_capital_injection(inject):
    base = E.run(E.build_config())
    cen = E.run(E.build_config(overrides={"programme": {"central_capital_per_robot": inject}}))
    cap = D.PLATFORMS["platform_b"]["capital"]
    assert cen["capital"]["trust_funded"] == pytest.approx(max(cap - inject, 0))
    assert cen["economic"]["net_present_cost"] == pytest.approx(base["economic"]["net_present_cost"])


@pytest.mark.parametrize("setting,mult", list(D.INSTRUMENT_PRICE_SETTINGS.items()))
def test_instrument_price_settings(setting, mult):
    assert E.build_config(instrument_price=setting)["platform"]["instruments_per_case"] == pytest.approx(1500 * mult)
    assert E.build_config(instrument_price=900)["platform"]["instruments_per_case"] == 900


def test_managed_service_and_per_procedure_contract_basis():
    pr = E.build_config(platform="platform_c", overrides={"robots": 2})
    pc = E.build_config(platform="platform_c", overrides={"robots": 2, "platform": {"contract_volume_basis":
                                                                                     "per_contract"}})
    assert E.platform_cost_year(pr, 1, 700)["detail"]["excess_fees"] == pytest.approx(100 * 1200)
    assert E.platform_cost_year(pc, 1, 700)["detail"]["excess_fees"] == pytest.approx(400 * 1200)
    pp = E.build_config(platform="custom_per_procedure", overrides={"robots": 2})
    assert E.platform_cost_year(pp, 1, 100)["fixed"] == pytest.approx(600 * 2500)


def test_price_targets_reproduce_target():
    ov = {"programme": {"central_capital_per_robot": 2_000_000}}
    r = E.run(E.build_config(overrides=ov))
    pt = r["price_targets"]
    for key, target in [("budget_neutral_price", 0.0),
                        ("price_for_target", pt["target_net_cost_per_bed_day"] * r["yearly"][2]["bed_days"])]:
        if pt[key] is not None:
            r2 = E.run(E.build_config(overrides=ov, instrument_price=pt[key]))
            assert r2["yearly"][2]["net_cost"] == pytest.approx(target, abs=1e-6)


def test_700_per_robot_is_advisory_not_a_cut():
    g = rota({(1, w, d, s): ("inguinal", 4) for w in (1, 2) for d in D.WEEKDAYS for s in ("AM", "PM")})
    r = E.run(tcfg(g))
    assert r["yearly"][2]["cases"] == pytest.approx(80 * 22.5)          # 1,800, not cut
    assert any("(advisory)" in w for w in r["warnings"])
    assert next(x for x in r["guardrails"] if x["check"] == "Robotic operations per robot per year")["status"] == "amber"


def test_cancellation_factor_scales_delivery():
    a = E.run(E.build_config("large_1"))
    b = E.run(E.build_config("large_1", overrides={"programme": {"realisation_factor": 0.9}}))
    assert b["yearly"][2]["cases"] == pytest.approx(0.9 * a["yearly"][2]["cases"])


def test_tariff_enters_cash_case_only():
    base = E.run(E.build_config("large_1"))
    r = E.run(E.build_config("large_1", overrides={"groups": {"prostatectomy": {"tariff_uplift": 500.0}}}))
    for y0, y in zip(base["yearly"], r["yearly"]):
        assert y["tariff_income"] == pytest.approx(500 * y["by_group"]["prostatectomy"]["cases"])
        assert y["extra_cost"] == pytest.approx(y0["extra_cost"])
    assert r["economic"]["net_present_cost"] == pytest.approx(base["economic"]["net_present_cost"])


# ---------------------------------------------------------------------------
# I. Benchmark, sensitivity, register
# ---------------------------------------------------------------------------
def test_benchmark():
    cases = BM.benchmark_cases()
    assert sum(cases.values()) == pytest.approx(550)
    trust = E.build_config(overrides={"programme": {"central_capital_per_robot": 1_000_000}})
    b = BM.run_benchmark(trust)
    assert b["cases_per_robot"] == pytest.approx(550) and b["config"]["programme"]["central_capital_per_robot"] == 1e6
    rows = BM.comparison_rows(E.run(trust), b)
    assert len(rows) == 9 and all(x[3] for x in rows)


@pytest.mark.parametrize("metric", list(S.METRICS))
def test_tornado_base_and_ordering(metric):
    cfg = E.build_config("large_2")
    r = E.run(cfg)
    t = S.tornado(cfg, metric, r)
    assert t["base"] == pytest.approx(S.metric_value(r, metric))
    sw = [b["swing"] for b in t["bars"]]
    assert sw == sorted(sw, reverse=True) and sw


def test_tornado_includes_prostatectomy_and_cancellations():
    names = [b["name"] for b in S.tornado(E.build_config("large_1"), "cost_per_bed_day")["bars"]]
    assert "Prostatectomy comparator" in names and "Bed-days saved per operation" in names
    names = [b["name"] for b in S.tornado(E.build_config("large_1"), "extra_cost")["bars"]]
    assert "Share of rota operations that go ahead" in names


def test_register_rows():
    rows = RX.register_rows()
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == 254
    for r in rows:
        assert r["specialty"] and r["source"] and r["status"] in RG.STATUSES
    assert not any(i.split(".")[-1] in RX.REMOVED_FIELDS or i.startswith("sp_") for i in ids)


def test_register_excel_layout_and_protection(tmp_path):
    from openpyxl import load_workbook
    p = tmp_path / "reg.xlsx"
    RX.export(str(p))
    ws = load_workbook(p)["Register"]
    assert [c.value for c in ws[1]] == RX.COLUMNS and ws.protection.sheet is True
    for name in RX.COLUMNS:
        assert ws.cell(row=2, column=RX.COLUMNS.index(name) + 1).protection.locked == (name in ("ID", "Value"))
    assert ws.cell(row=1, column=1).font.color.rgb.endswith("000000")


def _review(tmp_path, edits, extra=None):
    from openpyxl import load_workbook
    p = tmp_path / "reg.xlsx"
    RX.export(str(p))
    wb = load_workbook(p)
    ws = wb["Register"]
    ws.protection.sheet = False
    for row in ws.iter_rows(min_row=2):
        if row[0].value in edits:
            dec, val, com, src, grade = (list(edits[row[0].value]) + [None, None])[:5]
            row[9].value, row[10].value, row[11].value = dec, val, com
            if src:
                row[6].value = src
            if grade:
                row[7].value = grade
    for vals in extra or []:
        ws.append(vals)
    wb.save(p)
    return RX.load(p.read_bytes())


def test_register_reload_errors_and_sources(tmp_path):
    rev = _review(tmp_path, {
        "colectomy.extra_minutes_lap": ("change to", 45, "local audit", "Local audit 2026 (n=60)", "Observational"),
        "benign_gyn.p_open": ("change to", "55%", None),
        "rectal.comp_reduction_lap": (None, 0.02, None),                 # change-to value without decision
        "liver.los_reduction_open": ("change to", "lots", None),         # wrong type
        "breast.p_open": ("change to", 1.5, None),                       # share above 1
        "inguinal.p_open": ("maybe", None, None),                        # unknown decision
        "prostatectomy.p_open": ("needs evidence", None, "check national data")},
        extra=[("colectomy.cases_per_session", None, None, None, None, None, None, None, None, "change to", 1, None),
               ("sp_nephrectomy.share.open", None, None, None, None, None, None, None, None, "agree", None, None)])
    assert rev["changes"] == {"colectomy.extra_minutes_lap": 45.0, "benign_gyn.p_open": 0.55}
    assert rev["sources"]["colectomy.extra_minutes_lap"] == {"source": "Local audit 2026 (n=60)",
                                                              "grade": "Observational"}
    assert rev["needs_evidence"] == ["prostatectomy.p_open"]
    errs = " ".join(rev["errors"])
    assert len(rev["errors"]) == 6
    assert "without the decision 'change to'" in errs and "wrong type of value" in errs
    assert "share must lie between 0 and 1" in errs and "not recognised" in errs
    assert errs.count("no longer used from v0.8") == 2
    case = json.load(open(EX / "example_case.json"))
    case["configuration"]["register_review"] = rev
    cfg = E.build_config(**BC.configure(case))
    assert cfg["groups"]["colectomy"]["extra_minutes_lap"] == 45 and cfg["groups"]["benign_gyn"]["p_open"] == 0.55
    text = all_text(BC.build_blocks(case, include_charts=False)[0])
    assert "Local audit 2026 (n=60); Observational" in text and "check national data" in text


def test_register_rejects_wrong_file():
    from openpyxl import Workbook
    buf = io.BytesIO()
    Workbook().save(buf)
    assert RX.load(buf.getvalue())["errors"] == ["No 'Register' sheet found."]


# ---------------------------------------------------------------------------
# J. Business case and Word document
# ---------------------------------------------------------------------------
SUPPLIERS = ["da Vinci", "Intuitive", "Versius", "CMR", "Hugo", "Medtronic", "Senhance", "Asensus", " Xi"]


def all_text(blocks):
    out = []
    for b in blocks:
        for k in ("text", "title", "subtitle", "footnote", "caption"):
            if isinstance(b.get(k), str):
                out.append(b[k])
        out += b.get("items", [])
        if b["type"] == "table":
            out += b["header"]
            for row in b["rows"]:
                out += [str(x) for x in row]
        if b["type"] == "cover":
            out += [f"{a} {c}" for a, c in b["fields"]]
    return "\n".join(out)


@pytest.mark.parametrize("preset", D.PRESETS)
@pytest.mark.parametrize("platform", PLATFORMS)
def test_business_case_blocks_build(preset, platform):
    case = {"cover": {"trust_name": "Test Trust"},
            "configuration": {"preset": preset, "robots": D.PRESETS[preset]["robots"], "platform": platform,
                              "instrument_price": "standard_discount", "central_capital_per_robot": 1_000_000}}
    blocks, r = BC.build_blocks(case, include_charts=False)
    heads = [b["text"] for b in blocks if b["type"] == "h1"]
    for h in ("1. Executive summary", "2. Strategic case", "3. Economic case", "4. Commercial case",
              "5. Financial case", "6. Management case", "Appendix A. Clinical assumptions by specialty",
              "Appendix D. References"):
        assert h in heads
    text = all_text(blocks)
    for s in SUPPLIERS:
        assert s not in text, s
    assert not re.search(r"\b[a-z]+_[a-z_]+\b", text), re.findall(r"\b[a-z]+_[a-z_]+\b", text)[:5]
    assert "Option 1: the proposal as entered" in text and "Option 2" not in text
    assert "6.1 Two-week robot rota" in text and "demand" not in text.lower().replace("on-demand", "")


def test_executive_summary_order_and_flags():
    blocks, _ = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    h3 = [b["text"] for b in blocks if b["type"] == "h3"]
    i = [h3.index(x) for x in ("What the programme delivers for patients each year (year 3, steady state)",
                               "Cost per outcome (five years)", "Five-year cost to the trust")]
    assert i == sorted(i)
    text = all_text(blocks)
    assert "30-day benefit not yet modelled for" in text and "not a finding that the robot has no benefit" in text
    assert "set to neutral (zero) by the clinical lead for Complex cholecystectomy" in text
    assert "Neutral (clinical lead)" in text


def test_word_document_black_text_and_charts():
    from docx import Document
    data, _ = BC.build_docx_bytes({"cover": {"trust_name": "Test Trust"},
                                   "configuration": {"preset": "large_2", "robots": 2, "platform": "platform_b"}})
    doc = Document(io.BytesIO(data))
    assert "DRAFT" in doc.sections[0].header.paragraphs[0].text
    for p in doc.paragraphs:
        for run in p.runs:
            if run.font.color is not None and run.font.color.rgb is not None:
                assert str(run.font.color.rgb) == "000000", (p.text[:40], run.font.color.rgb)
    for name in ("Heading 1", "Heading 2", "Heading 3"):
        assert str(doc.styles[name].font.color.rgb) == "000000"
    xml = doc.tables[1]._tbl.xml
    assert 'w:fill="D9D9D9"' in xml and "1F3864" not in xml
    assert len(doc.inline_shapes) == 3


# ---------------------------------------------------------------------------
# K. v1.1.0: labels, wording, Word changes
# ---------------------------------------------------------------------------
NEW_LABELS = {
    "bariatric_antireflux": "Bariatric and anti-reflux surgery (gastric bypass, sleeve gastrectomy, fundoplication)",
    "colectomy": "Colectomy (right and left hemicolectomy, sigmoid colectomy)",
    "abdo_wall_repair": "Complex abdominal wall repair (incisional and ventral hernia, component separation)",
    "inguinal": "Complex inguinal hernia (recurrent, bilateral or large)",
    "liver": "Liver resection (hepatectomy, segmentectomy)",
    "lobectomy_transoral": "Lobectomy and transoral surgery (lung lobectomy, TORS)",
    "og_resection": "Oesophagogastric resection (oesophagectomy, gastrectomy)",
    "rectal": "Rectal resection (anterior resection, APR)",
}


def test_version_and_common_name_labels():
    assert D.ENGINE_VERSION == "1.1.0"
    for k, lab in NEW_LABELS.items():
        assert D.PROCEDURE_GROUPS[k]["label"] == lab
    ids = {r["id"] for r in RX.register_rows()}
    assert "rectal.los_reduction_lap" in ids and "og_resection.p_open" in ids      # IDs unchanged


@pytest.mark.parametrize("n,text", [("0", "The trust has no existing soft-tissue robots"),
                                    ("1", "The trust has one existing soft-tissue robot"),
                                    ("3", "The trust has three existing soft-tissue robots"),
                                    ("5 or more", "The trust has five or more existing soft-tissue robots")])
def test_existing_robots_wording(n, text):
    assert D.existing_robots_text(n) == text


def test_intro_and_not_modelled_notes():
    assert D.INTRO_LINE.startswith("A 30-day cost-consequence model to help you understand the best cost configuration")
    assert D.INTRO_LINE.endswith("It is not a QALY-based health economic model.")
    assert D.NOT_MODELLED_NOTE == "Simple cholecystectomy and simple inguinal hernia are not modelled."


_NOT_OPS = ["business", "Business", "base", "Base", "cash", "Cash", "economic", "Economic", "financial", "Financial",
            "commercial", "Commercial", "strategic", "Strategic", "management", "Management", "this", "This", "the",
            "The", "Five", "trust's", "hand-calculated"]
OPERATION_WORDS = re.compile("".join(f"(?<!{w} )" for w in _NOT_OPS) + r"\b[Cc]ases?\b(?! for)(?! study)")


@pytest.mark.parametrize("preset", ["medium_dgh_1", "large_2"])
def test_operations_wording_in_business_case(preset):
    case = {"cover": {}, "configuration": {"preset": preset, "robots": D.PRESETS[preset]["robots"],
                                           "platform": "platform_b"}}
    blocks, _ = BC.build_blocks(case, include_charts=False)
    body = all_text([b for b in blocks if b["type"] != "numbered"])        # references keep their titles
    hits = OPERATION_WORDS.findall(body)
    assert hits == [], [m.start() for m in OPERATION_WORDS.finditer(body)][:5]
    assert "operations a year" in body or "Operations a year" in body


def test_operations_wording_in_register():
    rows = RX.register_rows()
    text = " ".join(f"{r['assumption']} {r['unit']}" for r in rows)
    assert not OPERATION_WORDS.findall(text)
    assert any("per operation" in r["unit"] for r in rows)


def test_word_case_has_no_register_appendix_but_says_where_it_is():
    blocks, _ = BC.build_blocks(json.load(open(EX / "example_case.json")), include_charts=False)
    h1 = [b["text"] for b in blocks if b["type"] == "h1"]
    assert "Appendix D. Assumptions register" not in h1 and h1[-1] == "Appendix D. References"
    text = all_text(blocks)
    assert BC.REGISTER_LINE in text
    assert "Appendix A. Clinical assumptions by specialty" in h1


def test_word_headings_use_arial_without_theme_fonts():
    import zipfile
    data, _ = BC.build_docx_bytes(json.load(open(EX / "example_case.json")), include_charts=False)
    styles = zipfile.ZipFile(io.BytesIO(data)).read("word/styles.xml").decode()
    for sid in ("Heading1", "Heading2", "Heading3", "Title"):
        i = styles.index(f'w:styleId="{sid}"')
        block = styles[i:styles.index("</w:style>", i)]
        assert 'w:ascii="Arial"' in block and "asciiTheme" not in block and "hAnsiTheme" not in block, sid
