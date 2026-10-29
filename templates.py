"""
Two-week theatre template (v0.7): the main input.

Each robot has 14 days (Monday to Sunday, twice) x 3 sessions ("AM session 1",
"PM session 2", "PM session 3"). Each session holds ONE entry:

  ""             "Unfilled session": open but unbooked in standard hours (weekday
                 sessions 1 and 2); not in use for session 3 and weekends
  procedure key  a listed procedure ("Specialty - Procedure" on screen)
  "Maintenance"  not available (maintenance)
  "Closed"       not available

Cases per booked session come from each procedure's cases_per_session (set by its
complexity, editable). A whole-day procedure counts half a case per session and is
flagged if it is booked in only one session of a day.

Grid format (engine and saved inputs): a list with one entry per robot; each entry is
a list of 14 row dicts with keys week, day, AM, PM, Eve.
"""
import copy

import defaults as D

DASH = "\u2013"          # en dash between specialty and procedure


# ---------------------------------------------------------------------------
# Options and labels
# ---------------------------------------------------------------------------
def option_label(cfg, key):
    g = cfg["groups"][key]
    return f"{g['specialty']} {DASH} {g['label']}"


def procedure_keys(cfg):
    """Listed procedures in alphabetical order of procedure name (as in Aneel's list)."""
    return sorted((k for k in cfg["groups"] if k not in D.NOT_MODELLED),
                  key=lambda k: cfg["groups"][k]["label"].lower())


def options(cfg):
    """Dropdown options: unfilled first, procedures, then Maintenance and Closed."""
    return [D.UNFILLED] + [option_label(cfg, k) for k in procedure_keys(cfg)] + ["Maintenance", "Closed"]


def label_map(cfg):
    return {option_label(cfg, k): k for k in procedure_keys(cfg)}


def is_standard(day, session):
    return day in D.WEEKDAYS and session in ("AM", "PM")


def day_label(row):
    return f"Week {row['week']} {row['day']}"


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------
def empty_robot():
    rows = []
    for w in (1, 2):
        for d in D.DAYS:
            row = dict(week=w, day=d)
            for s in D.SESSIONS:
                row[s] = "Maintenance" if (d == "Fri" and s == "PM") else ""
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


# ---------------------------------------------------------------------------
# Summary: what the template books, per fortnight
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
            day_count = {}
            for s in D.SESSIONS:
                entry = (row.get(s, "") or "").strip()
                where = f"Robot {ri + 1}, week {row['week']} {row['day']} {D.SESSION_LABELS[s]}"
                status, ncases, proc = "unused", 0.0, ""
                if entry in ("Maintenance", "Closed"):
                    status = entry.lower()
                elif entry == "":
                    status = "open" if is_standard(row["day"], s) else "unused"
                elif entry in G:
                    status, proc = "booked", entry
                    ncases = G[entry]["cases_per_session"]
                    cases[entry] += ncases
                    sessions[entry] += 1
                    day_count[entry] = day_count.get(entry, 0) + 1
                else:
                    issues.append(f"{where}: '{entry}' is not a listed procedure; treated as unfilled.")
                    status = "open" if is_standard(row["day"], s) else "unused"
                if status == "booked":
                    booked += 1
                    available += 1
                elif status == "open":
                    available += 1
                cells.append(dict(robot=ri + 1, week=row["week"], day=row["day"], session=s, procedure=proc,
                                  status=status, cases=ncases))
            for k, n in day_count.items():
                if G[k].get("whole_day") and n % 2:
                    issues.append(f"Robot {ri + 1}, week {row['week']} {row['day']}: {G[k]['label']} is a whole-day "
                                  f"procedure but is booked for {n} session{'s' if n != 1 else ''}; book it in two "
                                  "sessions of the same day.")
    return dict(cases_per_fortnight=cases, booked=booked, available=available, issues=issues, cells=cells,
                procedure_sessions={k: n for k, n in sessions.items() if n}, group_sessions=dict(sessions))


# ---------------------------------------------------------------------------
# Suggest a template from demand (also builds the preset defaults)
# ---------------------------------------------------------------------------
def suggest_template(cfg, variant="standard", robots=None):
    """Fill a two-week grid from annual demand (group volumes).

    Sessions are filled in order (robot, weekday, week 1 then week 2, session 1 then 2;
    then, for the extended day only, Monday to Thursday session 3) until demand is met
    or sessions run out. A procedure keeps the rest of its day while it still has
    unmet demand; otherwise the session goes to the procedure needing the most
    sessions. A whole-day procedure is placed in session 1 and session 2 together.
    The target allows for the share of templated cases that go ahead.
    """
    robots = robots or cfg["robots"]
    f = cfg["programme"]["operating_weeks_per_year"] / 2
    real = cfg["programme"].get("realisation_factor", 1.0) or 1.0
    G = cfg["groups"]
    remaining = {k: g["volume"] / f / real for k, g in G.items() if k not in D.NOT_MODELLED}
    grid = empty_grid(robots)

    def need(k):
        return remaining[k] / G[k]["cases_per_session"] if G[k]["cases_per_session"] > 0 else 0.0

    def best(allow_whole_day, prev):
        if prev and remaining.get(prev, 0) > 1e-9 and not G[prev].get("whole_day"):
            return prev
        cands = [k for k in remaining if remaining[k] > 1e-9 and G[k]["cases_per_session"] > 0
                 and (allow_whole_day or not G[k].get("whole_day"))]
        return max(cands, key=lambda k: (need(k), k)) if cands else None

    passes = [["AM", "PM"]] + ([["Eve"]] if variant == "extended" else [])
    for sessions in passes:
        for ri in range(robots):
            for d in D.WEEKDAYS:
                for w in (1, 2):
                    row = next(x for x in grid[ri] if x["week"] == w and x["day"] == d)
                    prev = (row["PM"] or None) if sessions == ["Eve"] else None
                    for s in sessions:
                        if row[s]:          # already filled (whole-day pair or maintenance)
                            prev = row[s] if row[s] in G else None
                            continue
                        if d == "Fri" and s != "AM":
                            continue
                        whole_ok = s == "AM" and not row["PM"]
                        k = best(whole_ok, prev if prev in G else None)
                        if k is None:
                            prev = None
                            continue
                        row[s] = k
                        remaining[k] -= G[k]["cases_per_session"]
                        if G[k].get("whole_day"):
                            row["PM"] = k
                            remaining[k] -= G[k]["cases_per_session"]
                        prev = k
    return grid


# ---------------------------------------------------------------------------
# Web grid conversion: "Unfilled session" on screen, "" in the engine
# ---------------------------------------------------------------------------
UI_COLUMNS = ["Week", "Day"] + [D.SESSION_LABELS[s] for s in D.SESSIONS]


def to_ui_rows(cfg, robot_rows):
    lab = {k: option_label(cfg, k) for k in cfg["groups"]}
    out = []
    for row in robot_rows:
        d = {"Week": int(row["week"]), "Day": row["day"]}
        for s in D.SESSIONS:
            e = row.get(s, "") or ""
            d[D.SESSION_LABELS[s]] = lab.get(e, e) if e else D.UNFILLED
        out.append(d)
    return out


def _clean(v):
    if v is None or (isinstance(v, float) and v != v):
        return ""
    v = str(v).strip()
    return "" if v == D.UNFILLED else v


def from_ui_rows(cfg, records):
    rev = label_map(cfg)
    out = []
    for rec in records:
        row = dict(week=int(rec["Week"]), day=rec["Day"])
        for s in D.SESSIONS:
            v = _clean(rec.get(D.SESSION_LABELS[s]))
            row[s] = rev.get(v, v)
        out.append(row)
    return out


def cell_text(cfg, cell, short=True):
    if cell["status"] == "booked":
        g = cfg["groups"][cell["procedure"]]
        return g["label"].split(" (")[0] if short else option_label(cfg, cell["procedure"])
    if cell["status"] == "open":
        return "Unfilled"
    if cell["status"] in ("closed", "maintenance"):
        return cell["status"].capitalize()
    return ""
