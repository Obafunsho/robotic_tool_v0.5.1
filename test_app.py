"""Smoke and behaviour tests for the web interface (Streamlit AppTest, no browser needed)."""
import json
import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import defaults as D
import engine as E
import templates as T

EX = Path(__file__).parent / "examples"


def _app():
    at = AppTest.from_file("app.py", default_timeout=180)
    at.run()
    assert not at.exception, at.exception
    return at


def _grids(at):
    return [df for df in at.dataframe if df.proto.editing_mode and "Sessions available" in df.value.columns]


def test_app_loads_and_shows_results_in_fixed_order():
    at = _app()
    labels = [m.label for m in at.metric]
    assert labels.index("Robotic operations") < labels.index("Extra cost per bed-day released") \
        < labels.index("Five-year extra cost (revenue)")


def test_rota_is_the_main_input():
    at = _app()
    grids = _grids(at)
    assert len(grids) == 1
    g = grids[0].value
    assert list(g.columns) == T.ui_columns()
    assert list(g.columns)[:5] == ["Week", "Day", "Sessions available", "Session 1 (AM): procedure",
                                   "Session 1 cases"]
    assert len(g) == 14
    assert list(g["Sessions available"][:7]) == [2, 2, 2, 2, 2, 0, 0]
    assert g.iloc[0]["Session 1 (AM): procedure"] == "Rectal resection" and g.iloc[0]["Session 2 cases"] == "cont."
    vals = g.drop(columns=["Week", "Day", "Sessions available"]).values.ravel()
    assert not any(v is None or v == "" or v == "None" for v in vals)
    cfg = json.loads(grids[0].proto.columns)
    assert cfg["Sessions available"]["type_config"]["options"] == [0, 2, 3]
    assert cfg["Session 1 cases"]["type_config"]["options"] == [T.BLANK_CASES, "1", "2", "3", "4", "cont."]
    popts = cfg["Session 1 (AM): procedure"]["type_config"]["options"]
    assert popts[0] == "Unfilled session" and len(popts) == 18 and "Maintenance" not in popts


def test_hospital_type_only_changes_the_example_rota():
    at = _app()
    before = _grids(at)[0].value.iloc[0]["Session 1 (AM): procedure"]
    at.sidebar.radio(key="w_hospital").set_value("Large hospital (800 beds or more)").run()
    assert not at.exception, at.exception
    after = _grids(at)[0].value.iloc[0]["Session 1 (AM): procedure"]
    assert before == "Rectal resection" and after == "Radical prostatectomy"


def test_two_robots_give_two_prefilled_rotas():
    at = _app()
    at.sidebar.radio(key="w_robots").set_value(2).run()
    assert not at.exception, at.exception
    grids = _grids(at)
    assert len(grids) == 2
    assert (grids[1].value["Session 1 (AM): procedure"] != "Unfilled session").any()


def test_clear_rota_button():
    at = _app()
    next(b for b in at.button if b.label == "Clear the rota").click().run()
    assert not at.exception, at.exception
    g = _grids(at)[0].value
    assert (g["Session 1 (AM): procedure"] == "Unfilled session").all()
    labels = {m.label: m.value for m in at.metric}
    assert labels["Robotic operations"] == "0"


@pytest.mark.parametrize("platform", list(D.PLATFORMS))
def test_app_switches_platform(platform):
    at = _app()
    at.sidebar.selectbox(key="w_platform").set_value(platform).run()
    assert not at.exception, at.exception


def test_existing_robots_input():
    at = _app()
    sb = at.sidebar.selectbox(key="w_existing")
    assert list(sb.options) == D.EXISTING_ROBOT_OPTIONS
    sb.set_value("5 or more").run()
    assert not at.exception, at.exception


def test_prostatectomy_scenario():
    at = _app()
    at.sidebar.radio(key="w_hospital").set_value("Large hospital (800 beds or more)").run()
    at.sidebar.radio(key="w_prost").set_value("Robotic surgery at another centre").run()
    assert not at.exception, at.exception


def test_unit_costs_editable_in_advanced_section():
    at = _app()
    uc = next(df for df in at.dataframe if df.proto.editing_mode and "Value (£)" in df.value.columns)
    names = list(uc.value["Cost"])
    for n in ("Excess bed-day", "Extra theatre minute", "Sterile services per robotic case",
              "Surgical first assistant: cost per WTE"):
        assert n in names
    assert json.loads(uc.proto.columns)["key"]["hidden"] is True


def test_inputs_tables_hide_internal_columns():
    at = _app()
    for df in at.dataframe:
        if not df.proto.editing_mode:
            continue
        cfg = json.loads(df.proto.columns)
        for internal in ("group", "comparator", "key"):
            if internal in cfg:
                assert cfg[internal]["hidden"] is True, internal
        assert cfg.get("_index", {}).get("hidden") is True


def test_reloaded_case_keeps_its_rota_and_existing_robots():
    at = _app()
    case = json.load(open(EX / "example_case.json"))
    grid = T.empty_grid(1)
    grid[0][0].update(AM_proc="rectal", AM_cases="1", PM_proc="rectal", PM_cases="cont.")
    case["configuration"].update(template=grid, existing_robots="2")
    at.session_state["pending_case"] = case
    at.run()
    assert not at.exception, at.exception
    g = _grids(at)[0].value
    assert g.iloc[0]["Session 1 (AM): procedure"] == "Rectal resection" and g.iloc[0]["Session 2 cases"] == "cont."
    labels = {m.label: m.value for m in at.metric}
    assert labels["Sessions booked per fortnight"] == "2 of 20"
    assert at.session_state["w_existing"] == "2"


def test_cancellation_input_scales_results():
    at = _app()
    before = int(next(m.value for m in at.metric if m.label == "Robotic operations").replace(",", ""))
    at.sidebar.number_input(key="w_realisation").set_value(90).run()
    after = int(next(m.value for m in at.metric if m.label == "Robotic operations").replace(",", ""))
    assert abs(after - 0.9 * before) <= 1


def test_flags_on_results():
    at = _app()
    notes = " ".join(m.value for m in at.markdown)
    assert "30-day benefit not yet modelled for" in notes and "neutral (zero) by the clinical lead" in notes
    g = next(df for df in at.dataframe if "Check" in df.value.columns).value
    assert g[g["Check"] == "Procedures with 30-day benefit not yet modelled"].iloc[0]["Status"] == "Amber"


def test_tornado_labels_not_truncated():
    at = _app()
    spec = json.loads(at.get("vega_lite_chart")[-1].proto.spec)
    assert '"labelLimit": 0' in json.dumps(spec)


def test_register_download_offered():
    at = _app()
    assert "Download the assumptions register (.xlsx)" in [b.label for b in at.get("download_button")]


def test_app_generates_business_case():
    at = _app()
    at.text_input(key="c_trust_name").set_value("Example NHS Foundation Trust").run()
    next(b for b in at.button if b.label == "Generate Word business case").click().run()
    assert not at.exception, at.exception


def test_plain_theme_arial_black_text_and_no_emoji():
    import re
    root = Path(__file__).parent
    conf = tomllib.loads((root / ".streamlit" / "config.toml").read_text())
    assert conf["client"]["toolbarMode"] == "minimal"
    assert conf["theme"]["font"] == "Arial" and conf["theme"]["headingFont"] == "Arial"
    assert conf["theme"]["textColor"] == "#0B0C0C"
    src = (root / "app.py").read_text(encoding="utf-8")
    assert "NHS logo" not in src and not re.search("[\\U0001F300-\\U0001FAFF\\u2600-\\u27BF]", src)
