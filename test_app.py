"""Behaviour tests for the single-page web interface (Streamlit AppTest, no browser needed).
Visual checks (button and dropdown contrast) are made in Chromium; see the changelog."""
import json
import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import defaults as D
import templates as T

ROOT = Path(__file__).parent


def _app():
    at = AppTest.from_file("app.py", default_timeout=180)
    at.run()
    assert not at.exception, at.exception
    return at


def _grids(at):
    return [df for df in at.dataframe if df.proto.editing_mode and "Sessions available" in df.value.columns]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_single_page_main_view_is_minimal():
    at = _app()
    assert len(at.sidebar) == 0 or not list(at.sidebar)                 # no sidebar inputs
    main_keys = {w.key for w in list(at.selectbox) + list(at.radio)}
    assert {"w_hospital", "w_robots", "w_platform"} <= main_keys
    md = " ".join(m.value for m in at.markdown)
    assert D.INTRO_LINE in md
    labels = [m.label for m in at.metric]
    assert labels.index("Robotic operations") < labels.index("Extra cost per bed-day released") \
        < labels.index("Five-year extra cost (revenue)")
    assert [e.label for e in at.expander] == ["Advanced settings"]


def test_advanced_settings_hold_everything_else():
    at = _app()
    keys = {w.key for w in list(at.selectbox) + list(at.radio) + list(at.number_input) + list(at.checkbox)}
    for k in ("w_existing", "w_prost", "w_price_mode", "w_central", "w_evidence", "w_realisation", "w_capvalue"):
        assert k in keys, k
    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == ["Settings", "Prices, unit costs and tariff", "Procedures and clinical assumptions",
                          "Assumptions register", "Detailed results", "Sensitivity and benchmark", "Business case cover"]
    assert "Download the assumptions register (.xlsx)" in [b.label for b in at.get("download_button")]


def test_no_saved_case_reload_or_json_download():
    at = _app()
    uploaders = [u.proto.label for u in at.get("file_uploader")]
    assert uploaders == ["Load a reviewed register (.xlsx)"]
    labels = [b.label for b in at.get("download_button")]
    assert not any(".json" in lab for lab in labels)
    assert not (ROOT / "inputs_io.py").exists()


def test_rota_columns_use_operations_labels():
    at = _app()
    g = _grids(at)
    assert len(g) == 1
    cfg = json.loads(g[0].proto.columns)
    assert cfg["Session 1 operations"]["label"] == "Operations"
    assert cfg["Session 1 (AM): procedure"]["label"] == "Session 1 (AM)"
    assert cfg["Sessions available"]["type_config"]["options"] == [0, 2, 3]
    assert cfg["Session 2 operations"]["type_config"]["options"] == [T.BLANK_CASES, "1", "2", "3", "4", "cont."]
    v = g[0].value
    assert v.iloc[0]["Session 1 (AM): procedure"] == "Rectal resection (anterior resection, APR)"
    assert v.iloc[0]["Session 2 operations"] == "cont."
    assert len(v) == 14 and list(v["Sessions available"][:7]) == [2, 2, 2, 2, 2, 0, 0]
    captions = " ".join(c.value for c in at.caption)
    assert D.NOT_MODELLED_NOTE in captions


def test_hospital_type_changes_example_rota_and_two_robots():
    at = _app()
    at.selectbox(key="w_hospital").set_value("Large hospital (800 beds or more)").run()
    assert _grids(at)[0].value.iloc[0]["Session 1 (AM): procedure"] == "Radical prostatectomy"
    at.radio(key="w_robots").set_value(2).run()
    assert not at.exception and len(_grids(at)) == 2


@pytest.mark.parametrize("platform", list(D.PLATFORMS))
def test_platforms(platform):
    at = _app()
    at.selectbox(key="w_platform").set_value(platform).run()
    assert not at.exception, at.exception


def test_rota_warnings_only_when_rota_has_an_error():
    at = _app()
    assert not [w for w in at.warning if "Session" in w.value]
    next(b for b in at.button if b.label == "Clear the rota").click().run()
    assert _metric(at, "Robotic operations") == "0"


def test_cancellation_input_scales_results():
    at = _app()
    before = int(_metric(at, "Robotic operations").replace(",", ""))
    at.number_input(key="w_realisation").set_value(90).run()
    after = int(_metric(at, "Robotic operations").replace(",", ""))
    assert abs(after - 0.9 * before) <= 1


def test_existing_robots_and_prostatectomy_scenario():
    at = _app()
    at.selectbox(key="w_existing").set_value("5 or more").run()
    at.selectbox(key="w_hospital").set_value("Large hospital (800 beds or more)").run()
    at.radio(key="w_prost").set_value("Robotic surgery at another centre").run()
    assert not at.exception, at.exception


def test_unit_costs_and_tariff_in_advanced():
    at = _app()
    uc = next(df for df in at.dataframe if df.proto.editing_mode and "Cost" in df.value.columns)
    assert "Excess bed-day" in list(uc.value["Cost"])
    col = f"{D.TARIFF_FIELD_LABEL} (£ per operation)"
    tar = next(df for df in at.dataframe if df.proto.editing_mode and col in df.value.columns)
    v = tar.value
    assert float(v[v["Procedure"] == "Radical prostatectomy"][col].iloc[0]) == 3000.0


def test_flags_on_results():
    at = _app()
    notes = " ".join(m.value for m in at.markdown)
    assert "30-day benefit not yet modelled for" in notes and "neutral (zero) by the clinical lead" in notes


def test_generate_business_case_with_primary_buttons():
    at = _app()
    btn = next(b for b in at.button if b.label == "Generate Word business case")
    assert btn.proto.type == "primary"
    at.text_input(key="c_trust_name").set_value("Example NHS Foundation Trust").run()
    btn.click().run()
    assert not at.exception, at.exception
    dl = next(b for b in at.get("download_button") if b.label == "Download business case (.docx)")
    assert dl.proto.type == "primary"


def test_contrast_css_present():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'color: #FFFFFF !important' in src and '[role="option"]' in src
    conf = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    assert conf["theme"]["font"] == "Arial" and conf["client"]["toolbarMode"] == "minimal"
