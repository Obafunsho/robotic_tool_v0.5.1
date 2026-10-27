"""Smoke tests for the web interface (Streamlit AppTest, no browser needed)."""
import json
from pathlib import Path

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


def test_inputs_table_hides_internal_group_column():
    at = _app()
    cfg = json.loads(at.dataframe[0].proto.columns)
    assert cfg["group"]["hidden"] is True and cfg["_index"]["hidden"] is True
    assert "colorectal" not in [c for c in cfg if not cfg[c].get("hidden")]
    assert "Specialty" in at.dataframe[0].value.columns


def test_results_show_total_unmet_demand():
    at = _app()
    labels = {m.label: m.value for m in at.metric}
    assert labels["Total unmet demand (cases a year)"] == "0"
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
