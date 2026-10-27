"""
Save and reload a case. The website downloads the case (cover page plus
configuration) as JSON; this module checks an uploaded file and turns it into
the starting values for every input, so a saved case reproduces exactly.
Kept separate from app.py so it can be tested without a browser.
"""
import json

import defaults as D
import engine as E

HOSPITAL_LABELS = {"medium": "Medium DGH (under 800 beds)", "large": "Large hospital (800 beds or more)"}
COVER_FIELDS = ["trust_name", "prepared_by", "sro", "clinical_lead", "finance_lead", "version", "status", "date"]


def parse_case(data):
    """Parse and check an uploaded case. Returns (case, error message or None)."""
    try:
        case = json.loads(data) if isinstance(data, (bytes, str)) else data
    except (ValueError, UnicodeDecodeError):
        return None, "The file is not a valid inputs file (JSON could not be read)."
    if not isinstance(case, dict) or "configuration" not in case:
        return None, "The file has no 'configuration' section; was it saved by this tool?"
    c = case["configuration"]
    if c.get("preset") not in D.PRESETS:
        return None, "Unknown hospital type in the inputs file."
    if c.get("platform") not in D.PLATFORMS:
        return None, "Unknown platform in the inputs file."
    try:
        import business_case as BC
        E.build_config(**BC.configure(case))
    except (ValueError, KeyError, TypeError) as exc:
        return None, f"The inputs file could not be used: {exc}"
    case.setdefault("cover", {})
    return case, None


def widget_state(case):
    """Starting values for the website's inputs, keyed by widget key."""
    c = case["configuration"]
    size = "medium" if c["preset"].startswith("medium") else "large"
    ip = c.get("instrument_price", "list")
    st = {
        "w_hospital": HOSPITAL_LABELS[size],
        "w_robots": int(c.get("robots", D.PRESETS[c["preset"]]["robots"])),
        "w_platform": c["platform"],
        "w_price_mode": "custom" if isinstance(ip, (int, float)) else ip,
        "w_central": int(c.get("central_capital_per_robot", 0)),
        "w_evidence": c.get("evidence", "central"),
        "w_capvalue": bool(c.get("programme", {}).get("include_capacity_value", False)),
        "w_prost": ("Robotic surgery at another centre"
                    if c.get("groups", {}).get("prostatectomy", {}).get("p_robot_elsewhere", 0) >= 1
                    else "Open surgery"),
        "w_basis": c.get("platform_overrides", {}).get(
            "contract_volume_basis", D.PLATFORMS[c["platform"]].get("contract_volume_basis", "per_robot")),
    }
    if isinstance(ip, (int, float)):
        st["w_quote"] = float(ip)
    for f in COVER_FIELDS:
        if f in case.get("cover", {}):
            st[f"c_{f}"] = str(case["cover"][f])
    return st
