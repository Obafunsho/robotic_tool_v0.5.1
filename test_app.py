"""Smoke tests for the web interface (Streamlit AppTest, no browser needed)."""
import json
from pathlib import Path

import templates as T

import pytest
from streamlit.testing.v1 import AppTest

EX = Path(__file__).parent / "examples"


def _app():
    at = AppTest.from_file("app.py", default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def test_app_loads_and_shows_results_in_fixed_order():
    at = _app()
    labels = [m.label for m in at.metric]
    assert labels.index("Robotic operations") < labels.index("Extra cost per bed-day released") \
        < labels.index("Five-year extra cost (revenue)")


@pytest.mark.parametrize("platform", ["platform_a", "platform_c", "platform_d", "custom_per_procedure"])
def test_app_switches_platform(platform):
    at = _app()
    at.sidebar.selectbox(key="w_platform").set_value(platform).run()
    assert not at.exception, at.exception


def test_app_prostatectomy_scenario():
    at = _app()
    at.sidebar.radio(key="w_hospital").set_value("Large hospital (800 beds or more)").run()
    at.sidebar.radio(key="w_prost").set_value("Robotic surgery at another centre").run()
    assert not at.exception, at.exception


def test_app_reloads_saved_case():
    at = _app()
    case = json.load(open(EX / "example_case.json"))
    case["cover"]["trust_name"] = "Reloaded Trust"
    case["configuration"]["preset"] = "large_2"
    case["configuration"]["robots"] = 2
    at.session_state["pending_case"] = case
    at.run()
    assert not at.exception, at.exception
    assert at.session_state["w_robots"] == 2 and at.session_state["c_trust_name"] == "Reloaded Trust"
    assert at.session_state["w_central"] == 1_000_000


def test_app_generates_business_case():
    at = _app()
    at.text_input(key="c_trust_name").set_value("Example NHS Foundation Trust").run()
    gen = [b for b in at.button if b.label == "Generate Word business case"][0]
    gen.click().run()
    assert not at.exception, at.exception


def _editors(at):
    return {tuple(df.value.columns): df for df in at.dataframe if df.proto.editing_mode}


def test_inputs_tables_hide_internal_columns():
    at = _app()
    for df in at.dataframe:
        if not df.proto.editing_mode:
            continue
        cfg = json.loads(df.proto.columns)
        for internal in ("group", "comparator", "list_type", "tier"):
            if internal in cfg:
                assert cfg[internal]["hidden"] is True, internal
        assert cfg.get("_index", {}).get("hidden") is True
    demand = next(df for df in at.dataframe if "Annual demand" in df.value.columns)
    assert "Procedure" in demand.value.columns


def test_results_show_total_unmet_demand():
    at = _app()
    import engine as E
    labels = {m.label: m.value for m in at.metric}
    assert labels["Total unmet demand (cases a year)"] == f"{E.run(E.build_config())['unmet_cases']:,.0f}"
    case = json.load(open(EX / "example_case.json"))
    case["configuration"]["groups"] = {"colorectal": {"volume": 20000}}
    at.session_state["pending_case"] = case
    at.run()
    assert not at.exception, at.exception
    labels = {m.label: m.value for m in at.metric}
    assert int(labels["Total unmet demand (cases a year)"].replace(",", "")) > 19_000
    warns = " ".join(w.value for w in at.warning)
    assert "Colorectal major resection" in warns and "not scheduled" in warns


def test_tornado_labels_not_truncated():
    at = _app()
    spec = json.loads(at.get("vega_lite_chart")[-1].proto.spec)
    text = json.dumps(spec)
    assert '"labelLimit": 0' in text


def test_template_grid_is_the_main_input():
    at = _app()
    grids = [df for df in at.dataframe if "AM cases" in df.value.columns]
    assert len(grids) == 1
    g = grids[0].value
    assert len(g) == 14 and list(g.columns) == ["Day", "AM list", "AM cases", "PM list", "PM cases",
                                                "Evening list", "Evening cases"]
    assert g.iloc[0]["Day"] == "Week 1 Mon" and g.iloc[13]["Day"] == "Week 2 Sun"
    fri = g[g["Day"] == "Week 1 Fri"].iloc[0]
    assert fri["PM cases"] == "Maintenance"
    assert (g["Evening cases"] == T.BLANK).all()
    cfgs = json.loads(grids[0].proto.columns)
    assert "1 major + 1 medium + 1 minor" in cfgs["AM cases"]["type_config"]["options"]


def test_two_robots_give_two_grids_and_max_cases_changes_options():
    at = _app()
    at.sidebar.radio(key="w_robots").set_value(2).run()
    assert len([df for df in at.dataframe if "AM cases" in df.value.columns]) == 2
    at.sidebar.number_input(key="w_maxcases").set_value(4).run()
    assert not at.exception, at.exception
    g = next(df for df in at.dataframe if "AM cases" in df.value.columns)
    assert "4 minor" in json.loads(g.proto.columns)["AM cases"]["type_config"]["options"]


def test_extended_variant_books_evenings():
    at = _app()
    at.sidebar.radio(key="w_hospital").set_value("Large hospital (800 beds or more)").run()
    at.sidebar.radio(key="w_variant").set_value("extended").run()
    assert not at.exception, at.exception
    g = next(df for df in at.dataframe if "AM cases" in df.value.columns).value
    assert (g["Evening cases"] != "").any()


def test_reloaded_case_keeps_its_template():
    at = _app()
    case = json.load(open(EX / "example_case.json"))
    grid = [[dict(week=w, day=d, AM_list="", AM_cases="", PM_list="", PM_cases="", Eve_list="", Eve_cases="")
             for w in (1, 2) for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")]]
    grid[0][0].update(AM_list="colorectal", AM_cases="1 major")
    grid[0][4]["PM_cases"] = grid[0][11]["PM_cases"] = "Maintenance"
    case["configuration"]["template"] = grid
    at.session_state["pending_case"] = case
    at.run()
    assert not at.exception, at.exception
    g = next(df for df in at.dataframe if "AM cases" in df.value.columns).value
    assert g.iloc[0]["AM list"] == "Colorectal" and g.iloc[0]["AM cases"] == "1 major"
    assert (g.iloc[1:]["AM cases"] == T.BLANK).all()
    labels = {m.label: m.value for m in at.metric}
    assert labels["Sessions booked per fortnight"] == "1 of 18"


def test_institutional_theme_and_no_emoji():
    import re
    import tomllib
    root = Path(__file__).parent
    conf = tomllib.loads((root / ".streamlit" / "config.toml").read_text())
    assert conf["client"]["toolbarMode"] == "minimal"
    # v0.6.1: bundled faces (Source Sans, Source Serif); custom fontFaces fell back to Times in Chromium
    assert conf["theme"]["font"] == "sans-serif" and conf["theme"]["headingFont"] == "serif"
    assert "fontFaces" not in conf["theme"]
    emoji = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for f in ("app.py", "business_case.py"):
        assert not emoji.search((root / f).read_text(encoding="utf-8")), f


def test_grid_cells_never_none_or_empty():
    at = _app()
    for df in at.dataframe:
        if "AM cases" in df.value.columns:
            vals = df.value.drop(columns=["Day"]).values.ravel()
            assert not any(v is None or v == "" or v == "None" for v in vals)


def test_cancellation_input_scales_results():
    at = _app()
    before = int(next(m.value for m in at.metric if m.label == "Robotic operations").replace(",", ""))
    at.sidebar.number_input(key="w_realisation").set_value(90).run()
    assert not at.exception, at.exception
    after = int(next(m.value for m in at.metric if m.label == "Robotic operations").replace(",", ""))
    # delivery falls, but by less than 10% where the template schedules more than demand
    assert 0.9 * before - 1 <= after < before


def test_cap_guardrail_shown_as_advisory():
    at = _app()
    g = next(df for df in at.dataframe if "Check" in df.value.columns).value
    row = g[g["Check"] == "Robotic cases per robot per year"].iloc[0]
    assert row["Status"] == "Green" and "Advisory" in row["Rule"]
