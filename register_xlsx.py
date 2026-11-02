"""
Assumptions register as an Excel workbook for clinical review, and reading it back.

Export: one row per procedure and assumption, with a stable
ID, specialty, procedure, assumption, value, unit, source, evidence grade and status,
then blank review columns: Decision (agree / change to / needs evidence), Change to and
Comment. The ID and Value columns are locked (sheet protection, no password) so they
cannot be edited by accident; the review columns are unlocked.

Import: rows marked "change to" with a value become changes, keyed by ID; rows marked
"needs evidence" and any comments are kept for the business case, and the Source and
Evidence grade columns of changed rows are read so their citations reach Appendix D.
A "Change to" value without a Decision, a value of the wrong type, an unknown decision,
or a row no longer used by the model is reported as an error, not ignored. Changes are
applied by apply_changes() and appear as user-modified assumptions.
"""
import io
from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.worksheet.datavalidation import DataValidation

import defaults as D
import engine as E
import register as RG

COLUMNS = ["ID", "Specialty", "Procedure", "Assumption", "Value", "Unit", "Source", "Evidence grade", "Status",
           "Decision", "Change to", "Comment"]
WIDTHS = [30, 22, 38, 40, 12, 18, 60, 26, 18, 18, 14, 40]
DECISIONS = ["agree", "change to", "needs evidence"]
LOCKED = {"ID", "Value"}
NAVY = "1F3864"
FONT = "Arial"


def register_rows():
    """Every row for the procedure list (one row per procedure and assumption)."""
    return RG.detail_rows(E.build_config("large_1", "platform_b", template=None))


def export(path=None):
    rows = register_rows()
    wb = Workbook()
    readme = wb.active
    readme.title = "Read me"
    lines = [
        ("Robotic Programme Decision Tool: assumptions register for clinical review", True),
        (f"Engine version {D.ENGINE_VERSION}. Exported {date.today().strftime('%d %B %Y')}.", False),
        ("", False),
        ("How to review", True),
        ("1. Work in the 'Register' sheet. Each row is one assumption for one procedure.", False),
        ("2. In 'Decision', choose agree, change to, or needs evidence.", False),
        ("3. If you choose 'change to', enter the new value in 'Change to' in the same unit as 'Unit'.", False),
        ("   Shares and proportions may be entered as 0.45 or 45%. Complexity: High, Medium or Low.", False),
        ("4. Add any comment in 'Comment'.", False),
        ("5. Only the Decision, Change to and Comment columns need editing. ID and Value are locked so they "
         "cannot be changed by accident (the sheet is protected without a password).", False),
        ("6. Save the file and send it back; it is read into the tool and every change is flagged as "
         "user-modified in the business case.", False),
        ("", False),
        ("Example of a completed row (format only, not a recommendation)", True),
        ("ID: colectomy.extra_minutes_lap | Value: 40 | Decision: change to | Change to: 45 | "
         "Comment: local audit 2026", False),
        ("", False),
        ("Status key", True),
        ("Not yet modelled: 30-day benefit set to zero until the evidence is reviewed. Zero is a placeholder, "
         "not a finding that the robot has no benefit.", False),
        ("Neutral (clinical lead): 30-day effects set to zero by the clinical lead. Needs evidence: marked in the "
         "literature review; value kept.", False),
        ("Flagged for review: carried over from an earlier procedure group and needs specialty review.", False),
        ("Placeholder: no adequate source yet. Context only: national data for context, not the value itself.",
         False),
        ("Sourced / Partly sourced: from a cited publication; Assumption: a modelling choice; Clinical lead "
         "input: from Aneel's procedure list.", False),
    ]
    for i, (text, bold) in enumerate(lines, start=1):
        c = readme.cell(row=i, column=1, value=text)
        c.font = Font(name=FONT, bold=bold, size=12 if i == 1 else 10, color="000000")
    readme.column_dimensions["A"].width = 120

    ws = wb.create_sheet("Register")
    for j, (name, w) in enumerate(zip(COLUMNS, WIDTHS), start=1):
        c = ws.cell(row=1, column=j, value=name)
        c.font = Font(name=FONT, bold=True, color="000000")
        c.fill = PatternFill("solid", fgColor="D9D9D9")
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[c.column_letter].width = w
    review_fill = PatternFill("solid", fgColor="FFF8DC")
    status_fill = {"Not yet modelled": "FCE4D6", "Flagged for review": "FFF2CC", "Sourced": "E2EFDA",
                   "Partly sourced": "E2EFDA"}
    for i, r in enumerate(rows, start=2):
        values = [r["id"], r["specialty"], r["procedure"], r["assumption"], r["value"], r["unit"], r["source"],
                  r["grade"], r["status"], None, None, None]
        for j, (name, v) in enumerate(zip(COLUMNS, values), start=1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(name=FONT, size=9)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.protection = Protection(locked=name in LOCKED)
            if name in ("Decision", "Change to", "Comment"):
                c.fill = review_fill
            if name == "Status" and v in status_fill:
                c.fill = PatternFill("solid", fgColor=status_fill[v])
    dv = DataValidation(type="list", formula1='"' + ",".join(DECISIONS) + '"', allow_blank=True)
    dv.error, dv.errorTitle = "Choose agree, change to or needs evidence", "Decision"
    ws.add_data_validation(dv)
    dv.add(f"J2:J{len(rows) + 1}")
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = f"A1:L{len(rows) + 1}"
    ws.protection.sheet = True
    ws.protection.autoFilter = False      # filtering stays allowed
    ws.protection.sort = False
    ws.protection.formatColumns = False
    ws.protection.formatRows = False
    wb.active = 1
    if path:
        wb.save(path)
        return path
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Reading a reviewed register back
# ---------------------------------------------------------------------------
def _parse_value(id_, text):
    field = id_.split(".")[-1]
    s = str(text).strip()
    if field == "complexity":
        v = s.capitalize()
        if v not in D.COMPLEXITY_LEVELS:
            raise ValueError("complexity must be High, Medium or Low")
        return v
    pct = s.endswith("%")
    try:
        v = float(s.rstrip("%").replace(",", "").replace("£", "").strip())
    except ValueError:
        raise ValueError(f"'{s}' is not a number")
    if v < 0:
        raise ValueError("values cannot be negative")
    v = v / 100 if pct else v
    if field in ("p_open", "p_robot_elsewhere") and v > 1:
        raise ValueError("a share must lie between 0 and 1 (or 0% and 100%)")
    return v


REMOVED_FIELDS = ("demand_medium", "demand_large", "cases_per_session", "whole_day")


def load(data):
    """Read a reviewed register (path or bytes).
    Returns dict(changes, needs_evidence, comments, sources, errors)."""
    empty = dict(changes={}, needs_evidence=[], comments={}, sources={}, errors=[])
    wb = load_workbook(io.BytesIO(data) if isinstance(data, (bytes, bytearray)) else data, data_only=True)
    if "Register" not in wb.sheetnames:
        return dict(empty, errors=["No 'Register' sheet found."])
    ws = wb["Register"]
    head = [c.value for c in ws[1]]
    missing = [c for c in ("ID", "Decision", "Change to", "Comment") if c not in head]
    if missing:
        return dict(empty, errors=[f"Missing columns: {', '.join(missing)}."])
    ix = {name: head.index(name) for name in head if name}
    known = {r["id"]: r for r in register_rows()}
    changes, needs, comments, sources, errors = {}, [], {}, {}, []
    for n, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        id_ = row[ix["ID"]]
        if not id_:
            continue
        dec = str(row[ix["Decision"]] or "").strip().lower()
        new = row[ix["Change to"]]
        com = row[ix["Comment"]]
        if com:
            comments[id_] = str(com)
        if id_ not in known:
            if dec or new not in (None, ""):
                why = ("no longer used from v0.8 (cases come from the rota; demand and single-port removed)"
                       if id_.startswith("sp_") or id_.split(".")[-1] in REMOVED_FIELDS else "unknown ID")
                errors.append(f"Row {n} ({id_}): {why}; not applied.")
            continue
        if new not in (None, "") and dec != "change to":
            errors.append(f"Row {n} ({id_}): 'Change to' value {new!r} without the decision 'change to'"
                          + (f" (decision is '{dec}')" if dec else "") + "; not applied.")
            continue
        if dec == "change to":
            if new in (None, ""):
                errors.append(f"Row {n} ({id_}): 'change to' without a value; not applied.")
                continue
            try:
                changes[id_] = _parse_value(id_, new)
            except ValueError as exc:
                errors.append(f"Row {n} ({id_}): wrong type of value ({exc}); not applied.")
                continue
            sources[id_] = dict(source=str(row[ix["Source"]] or "") if "Source" in ix else "",
                                grade=str(row[ix["Evidence grade"]] or "") if "Evidence grade" in ix else "")
        elif dec == "needs evidence":
            needs.append(id_)
        elif dec and dec != "agree":
            errors.append(f"Row {n} ({id_}): decision '{dec}' not recognised; not applied.")
    return dict(changes=changes, needs_evidence=needs, comments=comments, sources=sources, errors=errors)


def apply_changes(overrides, changes, preset=None):
    """Apply register changes to build_config overrides (preset is accepted for saved cases
    from earlier versions and is not used: no calculation depends on the hospital type)."""
    groups = overrides.setdefault("groups", {})
    for id_, v in changes.items():
        parts = id_.split(".")
        if parts[0] == "unit_costs":
            overrides.setdefault("unit_costs", {})[parts[1]] = v
        elif parts[0] == "programme":
            overrides.setdefault("programme", {})[parts[1]] = v
        elif len(parts) == 2 and parts[0] in D.PROCEDURE_GROUPS:
            groups.setdefault(parts[0], {})[parts[1]] = v
    return overrides
