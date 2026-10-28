"""
Two-week theatre template (v0.6): the main input.

Each robot has 14 days (Monday to Sunday, twice) x 3 sessions (AM, PM, evening).
Each session holds a list type and a case entry: a combination of major, medium and
minor cases (up to the session maximum), or one of the special entries:

  ""            blank: open but unbooked in standard hours; not in use otherwise
  "Empty"       open but unbooked (use it to offer an evening or weekend session)
  "Continuing"  a case running on from the previous session on the same day
  "Closed"      not available
  "Maintenance" not available (maintenance)

Standard hours are weekday AM and PM. Tiers map to procedure groups through the
list-type mapping (editable). A tier mapped to nothing counts as "not modelled":
costs only, no 30-day benefit.

Grid format (engine and saved inputs): a list with one entry per robot; each entry is
a list of 14 row dicts with keys week, day, AM_list, AM_cases, PM_list, PM_cases,
Eve_list, Eve_cases. List values are list-type keys ("" for none).
"""
import copy
import itertools
import math
import re

import defaults as D

COMBO_RE = re.compile(r"(\d+)\s+(major|medium|minor)")


# ---------------------------------------------------------------------------
# Case entries
# ---------------------------------------------------------------------------
def format_combo(counts):
    parts = [f"{counts[t]} {t}" for t in D.TIERS if counts.get(t)]
    return " + ".join(parts)


def case_options(max_cases=3):
    """Every allowed case entry, specials first, then combinations up to max_cases."""
    combos = []
    for total in range(1, int(max_cases) + 1):
        for a, b in itertools.product(range(total, -1, -1), repeat=2):
            c = total - a - b
            if c < 0:
                continue
            combos.append(format_combo(dict(major=a, medium=b, minor=c)))
    seen, out = set(), []
    for x in combos:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return ["", "Empty", "Continuing"] + out + ["Closed", "Maintenance"]


def parse_cases(entry):
    """Return ("special", name) or ("combo", {tier: n}) or ("invalid", text)."""
    e = (entry or "").strip()
    if e in D.SPECIAL_ENTRIES:
        return "special", e
    found = COMBO_RE.findall(e)
    rebuilt = " + ".join(f"{n} {t}" for n, t in found)
    if not found or rebuilt != e:
        return "invalid", e
    counts = {t: 0 for t in D.TIERS}
    for n, t in found:
        counts[t] += int(n)
    return "combo", counts


# ---------------------------------------------------------------------------
# List types and mapping
# ---------------------------------------------------------------------------
def default_list_types(procedure_set="multiport"):
    return copy.deepcopy(D.SP_LIST_TYPES if procedure_set == "single_port" else D.LIST_TYPES)


def not_modelled_key(cfg):
    return "sp_not_modelled" if "sp_not_modelled" in cfg["groups"] else "not_modelled"


def validate_list_map(cfg):
    for lt, spec in cfg["list_map"].items():
        for t in D.TIERS:
            m = spec.get(t, [])
            for g, sh in m:
                if g not in cfg["groups"]:
                    raise ValueError(f"{spec['label']}, {t}: unknown procedure group '{g}'")
                if sh < 0:
                    raise ValueError(f"{spec['label']}, {t}: shares must not be negative")
            if m and abs(sum(sh for _, sh in m) - 1.0) > 1e-6:
                raise ValueError(f"{spec['label']}, {t}: the split must add up to 100%")


def mapping_rows(cfg):
    """Flat rows for the advanced mapping table."""
    rows = []
    for lt, spec in cfg["list_map"].items():
        for t in D.TIERS:
            m = spec.get(t, [])
            if not m:
                rows.append(dict(list_type=lt, tier=t, group="", share=1.0))
            for g, sh in m:
                rows.append(dict(list_type=lt, tier=t, group=g, share=float(sh)))
    return rows


def list_map_from_rows(rows, base):
    """Rebuild the mapping from edited rows. A blank group means not modelled."""
    out = copy.deepcopy(base)
    for lt in out:
        for t in D.TIERS:
            out[lt][t] = []
    for r in rows:
        if r["list_type"] in out and r.get("group") and float(r.get("share", 0)) > 0:
            out[r["list_type"]][r["tier"]].append([r["group"], float(r["share"])])
    return out


def modified_mapping(cfg, defaults_map):
    """Mapping entries that differ from the defaults, as readable items."""
    out = []
    for lt, spec in cfg["list_map"].items():
        d = defaults_map.get(lt, {})
        for t in D.TIERS:
            used = sorted((g, round(float(s), 6)) for g, s in spec.get(t, []))
            default = sorted((g, round(float(s), 6)) for g, s in d.get(t, []))
            if used != default:
                out.append(dict(item=f"list_map.{lt}.{t}", default=describe_split(cfg, default),
                                used=describe_split(cfg, used)))
    return out


def describe_split(cfg, pairs):
    if not pairs:
        return "not modelled"
    return ", ".join(f"{cfg['groups'][g]['label'] if g in cfg['groups'] else g} {s:.0%}" for g, s in pairs)


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------
def is_standard(day, session):
    return day in D.WEEKDAYS and session in ("AM", "PM")


def empty_robot():
    rows = []
    for w in (1, 2):
        for d in D.DAYS:
            row = dict(week=w, day=d)
            for s in D.SESSIONS:
                row[f"{s}_list"] = ""
                row[f"{s}_cases"] = "Maintenance" if (d == "Fri" and s == "PM") else ""
            rows.append(row)
    return rows


def empty_grid(robots):
    return [empty_robot() for _ in range(robots)]


def slots(grid):
    """Iterate (robot index, row index, week, day, session, list type, entry)."""
    for ri, robot in enumerate(grid):
        for i, row in enumerate(robot):
            for s in D.SESSIONS:
                yield ri, i, row["week"], row["day"], s, row.get(f"{s}_list", "") or "", row.get(f"{s}_cases", "") or ""


def label_of(cfg, lt):
    return cfg["list_map"][lt]["label"] if lt in cfg["list_map"] else lt


# ---------------------------------------------------------------------------
# Summary: what the template books, per fortnight
# ---------------------------------------------------------------------------
def summarise(cfg, grid=None):
    grid = cfg["template"] if grid is None else grid
    lm = cfg["list_map"]
    nm = not_modelled_key(cfg)
    maxn = cfg["programme"].get("max_cases_per_session", 3)
    cases = {k: 0.0 for k in cfg["groups"]}
    lt_sessions, lt_cases, issues, cells, lt_group = {}, {}, [], [], {}
    booked = available = 0
    tier_cases = {t: 0.0 for t in D.TIERS}
    for ri, robot in enumerate(grid):
        prev_booked_lt = None
        prev_day = None
        for i, row in enumerate(robot):
            for s in D.SESSIONS:
                lt = row.get(f"{s}_list", "") or ""
                entry = row.get(f"{s}_cases", "") or ""
                where = f"Robot {ri + 1}, week {row['week']} {row['day']} {D.SESSION_LABELS[s]}"
                if (row["week"], row["day"]) != prev_day:
                    prev_booked_lt, prev_day = None, (row["week"], row["day"])
                kind, val = parse_cases(entry)
                status, ncases = "unused", 0
                if lt and lt not in lm:
                    issues.append(f"{where}: unknown list type '{lt}'.")
                    lt = ""
                if kind == "invalid":
                    issues.append(f"{where}: '{entry}' is not a recognised case entry.")
                    kind, val = "special", ""
                if kind == "special":
                    if val in ("Closed", "Maintenance"):
                        status = val.lower()
                    elif val == "Continuing":
                        status = "booked"
                        if prev_booked_lt is None:
                            issues.append(f"{where}: 'Continuing' must follow a booked session earlier the same day.")
                        lt = lt or prev_booked_lt or ""
                    else:
                        if lt:
                            issues.append(f"{where}: list type chosen but no cases; treated as unbooked.")
                        status = "open" if (is_standard(row["day"], s) or val == "Empty" or lt) else "unused"
                        lt = ""
                else:
                    if not lt:
                        issues.append(f"{where}: cases entered without a list type; treated as unbooked.")
                        status = "open" if is_standard(row["day"], s) else "unused"
                    else:
                        status = "booked"
                        ncases = sum(val.values())
                        if ncases > maxn:
                            issues.append(f"{where}: {ncases} cases exceeds the session maximum of {maxn}.")
                        for t, n in val.items():
                            if not n:
                                continue
                            tier_cases[t] += n
                            m = lm[lt].get(t, [])
                            ltg = lt_group.setdefault(lt, {})
                            if not m:
                                cases[nm] += n
                                ltg[nm] = ltg.get(nm, 0) + n
                            for g, sh in m:
                                cases[g] += n * sh
                                ltg[g] = ltg.get(g, 0) + n * sh
                        lt_cases[lt] = lt_cases.get(lt, 0) + ncases
                if status == "booked":
                    booked += 1
                    available += 1
                    if lt:
                        lt_sessions[lt] = lt_sessions.get(lt, 0) + 1
                    prev_booked_lt = lt or prev_booked_lt
                elif status == "open":
                    available += 1
                    prev_booked_lt = None
                else:
                    prev_booked_lt = None
                cells.append(dict(robot=ri + 1, week=row["week"], day=row["day"], session=s, list_type=lt,
                                  entry=entry, status=status, cases=ncases))
    group_sessions = {k: 0.0 for k in cfg["groups"]}
    for lt, n in lt_sessions.items():
        tot = sum(lt_group.get(lt, {}).values())
        for g, c in lt_group.get(lt, {}).items():
            group_sessions[g] += n * c / tot if tot else 0.0
    return dict(cases_per_fortnight=cases, booked=booked, available=available, issues=issues,
                cells=cells, list_type_sessions=lt_sessions, list_type_cases=lt_cases, tier_cases=tier_cases,
                group_sessions=group_sessions)


# ---------------------------------------------------------------------------
# Suggest a template from demand (also builds the preset defaults)
# ---------------------------------------------------------------------------
def _trim(entry, lt_spec, remaining):
    """Reduce a pattern entry so no tier carries more cases than its groups still need."""
    kind, val = parse_cases(entry)
    if kind != "combo":
        return entry, {}
    counts, added = {}, {}
    for t in D.TIERS:
        n = val.get(t, 0)
        m = lt_spec.get(t, [])
        if not n or not m:
            counts[t] = 0
            continue
        need = max((max(remaining.get(g, 0.0), 0.0) / sh for g, sh in m if sh > 0), default=0.0)
        counts[t] = min(n, math.ceil(need - 1e-9)) if need > 1e-9 else 0
        for g, sh in m:
            added[g] = added.get(g, 0.0) + counts[t] * sh
    if not any(counts.values()):
        return "", {}
    return format_combo(counts), added


def _gain(added, remaining):
    return sum(min(max(remaining.get(g, 0.0), 0.0), c) for g, c in added.items())


def suggest_template(cfg, variant="standard", robots=None):
    """Fill a two-week grid from annual demand (group volumes).

    Sessions are filled in order (robot, weekday, week 1 then week 2, AM then PM;
    then, for the extended day only, Monday to Thursday evenings), until demand is
    met or sessions run out. Each
    session goes to the list type that adds the most demand still unmet, using its
    session pattern trimmed to the cases still needed; a list type keeps the rest of
    its day while it still adds cases (and a 'Continuing' case is always completed).
    The target allows for the share of templated cases that go ahead.
    """
    robots = robots or cfg["robots"]
    f = cfg["programme"]["operating_weeks_per_year"] / 2
    real = cfg["programme"].get("realisation_factor", 1.0) or 1.0
    remaining = {k: g["volume"] / f / real for k, g in cfg["groups"].items() if k not in D.NOT_MODELLED}
    positions = ["AM", "PM", "Eve"] if variant == "extended" else ["AM", "PM"]
    grid = empty_grid(robots)
    lts = {lt: spec for lt, spec in cfg["list_map"].items() if any(spec.get(t) for t in D.TIERS)}
    # pass 1: weekday AM and PM; pass 2 (extended day only): Monday to Thursday evenings
    passes = [["AM", "PM"]] + ([["Eve"]] if variant == "extended" else [])
    for sessions in passes:
        for ri in range(robots):
            for d in D.WEEKDAYS:
                for w in (1, 2):
                    row = next(x for x in grid[ri] if x["week"] == w and x["day"] == d)
                    prev_lt, prev_entry = None, ""
                    if sessions == ["Eve"]:
                        prev_lt, prev_entry = (row["PM_list"] or None), row["PM_cases"]
                    for s in sessions:
                        si = D.SESSIONS.index(s)
                        if d == "Fri" and s != "AM":
                            continue
                        choice = None
                        if (prev_lt and lts.get(prev_lt, {}).get("pattern", [""] * 3)[si] == "Continuing"
                                and prev_entry not in ("", "Continuing", "Maintenance")):
                            choice = (prev_lt, "Continuing", {})
                        else:
                            options = []
                            for lt, spec in lts.items():
                                entry = spec["pattern"][si]
                                if entry == "Continuing":
                                    entry = spec["pattern"][0]
                                entry, added = _trim(entry, spec, remaining)
                                gain = _gain(added, remaining)
                                if gain > 1e-9:
                                    options.append((lt == prev_lt, gain, lt, entry, added))
                            if options:
                                keep = [o for o in options if o[0]]
                                best = keep[0] if keep else max(options, key=lambda o: (o[1], o[2]))
                                choice = (best[2], best[3], best[4])
                        if choice is None:
                            prev_lt, prev_entry = None, ""
                            continue
                        lt, entry, added = choice
                        row[f"{s}_list"], row[f"{s}_cases"] = lt, entry
                        for g, c in added.items():
                            remaining[g] = remaining.get(g, 0.0) - c
                        prev_lt, prev_entry = lt, entry
    return grid


def resize(grid, robots):
    """Pad with empty robots or drop extra ones."""
    g = copy.deepcopy(grid)[:robots]
    while len(g) < robots:
        g.append(empty_robot())
    return g


def to_rows(robot_grid):
    return copy.deepcopy(robot_grid)


def day_label(row):
    return f"Week {row['week']} {row['day']}"


# ---------------------------------------------------------------------------
# Web grid conversion. Streamlit's editable grid shows an empty-string cell in a
# dropdown column as "None"; a non-breaking space displays as blank. It is used only
# on screen and converted back to "" here.
# ---------------------------------------------------------------------------
BLANK = "\u00a0"


def ui_options(options):
    return [BLANK if o == "" else o for o in options]


def to_ui_rows(robot_rows, lt_label):
    """Engine rows -> grid rows for the web editor (labels, blanks shown as BLANK)."""
    out = []
    for row in robot_rows:
        d = {"Day": day_label(row)}
        for s in D.SESSIONS:
            lab = D.SESSION_LABELS[s]
            d[f"{lab} list"] = lt_label.get(row.get(f"{s}_list", "") or "", "") or BLANK
            d[f"{lab} cases"] = (row.get(f"{s}_cases", "") or "") or BLANK
        out.append(d)
    return out


def _clean(v):
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return str(v).replace(BLANK, "").strip()


def from_ui_rows(records, lt_from_label):
    """Web editor rows -> engine rows (list-type keys, "" for blanks)."""
    out = []
    for rec in records:
        _, w, d = rec["Day"].split()
        row = dict(week=int(w), day=d)
        for s in D.SESSIONS:
            lab = D.SESSION_LABELS[s]
            row[f"{s}_list"] = lt_from_label.get(_clean(rec.get(f"{lab} list")), "")
            row[f"{s}_cases"] = _clean(rec.get(f"{lab} cases"))
        out.append(row)
    return out
