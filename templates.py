"""
Two-week robot rota (v0.8): the main input, mirroring the clinical lead's rota.

Each robot has 14 days (Monday to Sunday, twice). For each day:
  sessions    "Sessions available": 0, 2 or 3 (session 3 only on 3-session days)
and for each session (AM, PM, Eve = sessions 1, 2, 3):
  {s}_proc    procedure key, or "" for an unfilled session
  {s}_cases   1, 2, 3 or 4, or "cont." for a case continuing from the previous session
              with the same procedure (a case may span at most 3 sessions)

Utilisation = sessions booked / sessions available. A session is booked when it has a
procedure. Cases come only from the rota; complexity is descriptive.

Grid format (engine and saved inputs): a list with one entry per robot; each entry is a
list of 14 row dicts with keys week, day, sessions, AM_proc, AM_cases, PM_proc, PM_cases,
Eve_proc, Eve_cases.
"""
import copy

import defaults as D

BLANK_CASES = "\u2013"      # en dash shown for an empty cases cell (avoids "None" on screen)


# ---------------------------------------------------------------------------
# Options and labels
# ---------------------------------------------------------------------------
def procedure_keys(cfg):
    """Listed procedures in alphabetical order of procedure name (as in the clinical lead's list)."""
    return sorted(cfg["groups"], key=lambda k: cfg["groups"][k]["label"].lower())


def procedure_options(cfg):
    return [D.UNFILLED] + [cfg["groups"][k]["label"] for k in procedure_keys(cfg)]


def label_map(cfg):
    return {cfg["groups"][k]["label"]: k for k in procedure_keys(cfg)}


def case_options():
    return [BLANK_CASES] + D.CASE_OPTIONS


def day_label(row):
    return f"Week {row['week']} {row['day']}"


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------
def empty_robot():
    rows = []
    for w in (1, 2):
        for d in D.DAYS:
            row = dict(week=w, day=d, sessions=D.DEFAULT_SESSIONS[d])
            for s in D.SESSIONS:
                row[f"{s}_proc"], row[f"{s}_cases"] = "", ""
            rows.append(row)
    return rows


def empty_grid(robots):
    return [empty_robot() for _ in range(robots)]


def resize(grid, robots):
    """Pad with empty robots or drop extra ones."""
    g = copy.deepcopy(grid)[:robots]
    while len(g) < robots:
        g.append(empty_robot())
    return g


def example_rota(hospital, robots):
    """The starting example rota for a hospital type ('medium' or 'large')."""
    grid = empty_grid(robots)
    for ri, spec in enumerate(D.EXAMPLE_ROTAS[hospital][:robots]):
        for (w, d), entries in spec.items():
            row = next(x for x in grid[ri] if x["week"] == w and x["day"] == d)
            for s, (proc, cases) in zip(D.SESSIONS, entries):
                row[f"{s}_proc"], row[f"{s}_cases"] = proc, str(cases)
    return grid


def available_sessions(row):
    n = int(row.get("sessions", 0) or 0)
    return D.SESSIONS[:n] if n in (2, 3) else []


# ---------------------------------------------------------------------------
# Summary: what the rota books, per fortnight
# ---------------------------------------------------------------------------
def summarise(cfg, grid=None):
    grid = cfg["template"] if grid is None else grid
    G = cfg["groups"]
    cases = {k: 0.0 for k in G}
    sessions = {k: 0 for k in G}
    issues, cells = [], []
    booked = available = 0
    for ri, robot in enumerate(grid):
        for row in robot:
            n = row.get("sessions", 0)
            if n not in D.SESSIONS_AVAILABLE_OPTIONS:
                issues.append(f"Robot {ri + 1}, {day_label(row)}: sessions available must be 0, 2 or 3; "
                              "treated as 0.")
            avail = available_sessions(row)
            available += len(avail)
            prev_proc, span = "", 0
            for s in D.SESSIONS:
                where = f"Robot {ri + 1}, {day_label(row)} {D.SESSION_LABELS[s]}"
                proc = (row.get(f"{s}_proc") or "").strip()
                c = str(row.get(f"{s}_cases") or "").strip()
                status, ncases = "unused", 0
                if s not in avail:
                    if proc or c:
                        issues.append(f"{where}: not available on this day (sessions available "
                                      f"{n}); entry ignored.")
                    prev_proc, span = "", 0
                elif not proc:
                    status = "open"
                    if c:
                        issues.append(f"{where}: cases entered without a procedure; ignored.")
                    prev_proc, span = "", 0
                elif proc not in G:
                    issues.append(f"{where}: '{proc}' is not a listed procedure; treated as unfilled.")
                    status = "open"
                    prev_proc, span = "", 0
                else:
                    status = "booked"
                    sessions[proc] += 1
                    if c == D.CONT:
                        if proc != prev_proc:
                            issues.append(f"{where}: 'cont.' must follow a session with the same procedure on "
                                          "the same day.")
                            span = 1
                        else:
                            span += 1
                            if span > D.MAX_SESSIONS_PER_CASE:
                                issues.append(f"{where}: a case can span at most {D.MAX_SESSIONS_PER_CASE} "
                                              "sessions.")
                    elif c in D.CASE_OPTIONS:
                        ncases = int(c)
                        cases[proc] += ncases
                        span = 1
                    else:
                        issues.append(f"{where}: no cases entered for {G[proc]['label']}; counted as booked with "
                                      "no cases.")
                        span = 1
                    prev_proc = proc
                if status == "booked":
                    booked += 1
                cells.append(dict(robot=ri + 1, week=row["week"], day=row["day"], session=s, procedure=proc
                                  if status == "booked" else "", cases_entry=c, status=status, cases=ncases))
    return dict(cases_per_fortnight=cases, booked=booked, available=available, issues=issues, cells=cells,
                procedure_sessions={k: v for k, v in sessions.items() if v}, group_sessions=dict(sessions))


# ---------------------------------------------------------------------------
# Web grid conversion
# ---------------------------------------------------------------------------
def ui_columns():
    cols = ["Week", "Day", "Sessions available"]
    for i, s in enumerate(D.SESSIONS, start=1):
        cols += [f"{D.SESSION_LABELS[s]}: procedure", f"Session {i} cases"]
    return cols


def to_ui_rows(cfg, robot_rows):
    lab = {k: g["label"] for k, g in cfg["groups"].items()}
    out = []
    for row in robot_rows:
        d = {"Week": int(row["week"]), "Day": row["day"], "Sessions available": int(row.get("sessions", 0) or 0)}
        for i, s in enumerate(D.SESSIONS, start=1):
            p = row.get(f"{s}_proc", "") or ""
            d[f"{D.SESSION_LABELS[s]}: procedure"] = lab.get(p, p) if p else D.UNFILLED
            d[f"Session {i} cases"] = str(row.get(f"{s}_cases", "") or "") or BLANK_CASES
        out.append(d)
    return out


def _clean(v, blank):
    if v is None or (isinstance(v, float) and v != v):
        return ""
    v = str(v).strip()
    return "" if v == blank else v


def from_ui_rows(cfg, records):
    rev = label_map(cfg)
    out = []
    for rec in records:
        try:
            n = int(float(rec.get("Sessions available") or 0))
        except (TypeError, ValueError):
            n = 0
        row = dict(week=int(rec["Week"]), day=rec["Day"], sessions=n)
        for i, s in enumerate(D.SESSIONS, start=1):
            p = _clean(rec.get(f"{D.SESSION_LABELS[s]}: procedure"), D.UNFILLED)
            row[f"{s}_proc"] = rev.get(p, p)
            row[f"{s}_cases"] = _clean(rec.get(f"Session {i} cases"), BLANK_CASES)
        out.append(row)
    return out


def cell_text(cfg, cell):
    if cell["status"] == "booked":
        name = cfg["groups"][cell["procedure"]]["label"].split(" (")[0]
        c = cell["cases_entry"]
        return f"{name} ({c})" if c else name
    if cell["status"] == "open":
        return "Unfilled"
    return ""
