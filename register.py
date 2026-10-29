"""
Assumptions register: every input the business case depends on, with the value
used, its source, an evidence grade, its status and who must sign it off.

Two views from one source:
  detail_rows() : one row per procedure and assumption, with a stable ID; exported to
                  Excel for clinical review (register_xlsx.py) and read back in
  rows()        : a compact view for the Word business case and the website

Status values
  Sourced             : taken from a cited publication or policy document
  Partly sourced      : a source supports the direction or size, but the value is a judgement
  Context only        : a source gives national context but not the value itself
  Placeholder         : no adequate source yet; must be replaced or confirmed
  Not yet modelled    : 30-day benefit set to zero until evidence is reviewed (not "no benefit")
  Flagged for review  : a value known to need clinical review before use
  Clinical lead input : set by the clinical lead (Aneel's procedure list)
  Assumption          : a modelling choice made by the project team
  Trust input         : entered by the trust; to be evidenced locally
Nothing is marked as reviewed: specialty review is pending.
"""
import defaults as D
import engine as E

STATUSES = ("Sourced", "Partly sourced", "Context only", "Placeholder", "Not yet modelled", "Flagged for review",
            "Clinical lead input", "Assumption", "Trust input")

SRC = dict(
    nboca="NBOCA State of the Nation report 2025",
    surg_endosc_2024="Surg Endosc 2024 (US registry, conversion 9.8% v 4.8%)",
    plos_2015="Trastulli et al, PLoS One 2015 (length of stay -0.68 days v laparoscopy)",
    hyst="Clark and Saridogan 2021, citing Madhvani et al (about half laparoscopic, 2011-17)",
    hernia="World J Emerg Surg 2025 (open repair commonest in UK national data)",
    nice="NICE HealthTech guidance 742 (early value assessment HTE21), April 2025",
    girft="NHS England and GIRFT, Implementation of robotic-assisted surgery in England, July 2025",
    donald="Donald et al, Surg Endosc 2026",
    pq="UK Parliament written answer UIN 100046, December 2025 (elective bed-day £1,198, 2024/25)",
    green="HM Treasury Green Book (3.5% discount rate)",
    aua="AUA 2022 abstract MP32-10",
    rival="Prabhu et al, RIVAL randomised trial, JAMA Surg 2020;155:380-87",
    robot="van der Sluis et al, ROBOT randomised trial, Ann Surg 2019;269:621-30",
    europa="Klotz et al, EUROPA randomised trial, Lancet Reg Health Eur 2024;39:100864",
    kalata="Kalata et al, JAMA Surg 2023;158:1303-10 (US Medicare cohort)",
    toesca="Toesca et al, randomised trial, Ann Surg 2022;276:11-19",
    nessa="Nessa et al, meta-analysis, BJS 2024;111:znad336",
    liver_ma="Systematic review and meta-analysis of 2,728 robotic liver resections (2022)",
    aneel="Clinical lead's procedure list and complexity ratings (October 2026)",
)

NEW_EVIDENCE = {   # (source, evidence grade) for procedures whose 30-day benefit is not yet modelled
    "breast": (f"{SRC['toesca']}: complications similar, robotic v open nipple-sparing mastectomy; {SRC['nessa']}: "
               "less nipple necrosis, longer stay", "Randomised trial (single centre) and meta-analysis"),
    "cholecystectomy": (f"{SRC['kalata']}: more bile duct injury with robotic than laparoscopic (possible harm)",
                        "Observational (large national cohort)"),
    "inguinal": (f"{SRC['rival']}: no 30-day differences v laparoscopic; longer and costlier", "Randomised trial"),
    "liver": (f"{SRC['liver_ma']}: shorter stay and fewer complications v open; no randomised trial found",
              "Meta-analysis of observational studies"),
    "og_resection": (f"{SRC['robot']}: surgery-related complications 59% v 80% (robot-assisted v open)",
                     "Randomised trial (single centre)"),
    "whipple": (f"{SRC['europa']}: no difference in 90-day morbidity v open; more pancreas-specific complications",
                "Randomised trial (single centre)"),
}

EFFECTS = [("los_reduction_open", "Bed-days saved v open", "days per case"),
           ("los_reduction_lap", "Bed-days saved v laparoscopic", "days per case"),
           ("conv_reduction_lap", "Conversions avoided v laparoscopic", "proportion per case"),
           ("comp_reduction_open", "Major complications avoided v open", "proportion per case"),
           ("comp_reduction_lap", "Major complications avoided v laparoscopic", "proportion per case"),
           ("reop_reduction_open", "Returns to theatre avoided v open", "proportion per case"),
           ("reop_reduction_lap", "Returns to theatre avoided v laparoscopic", "proportion per case"),
           ("readm_reduction_open", "Readmissions avoided v open", "proportion per case"),
           ("readm_reduction_lap", "Readmissions avoided v laparoscopic", "proportion per case"),
           ("extra_minutes_open", "Extra theatre minutes v open", "minutes per case"),
           ("extra_minutes_lap", "Extra theatre minutes v laparoscopic", "minutes per case")]

FLAGGED_CARRY = {
    "rectal": "Carried over from colorectal major resection; rectal-specific evidence not yet reviewed",
    "abdo_wall_repair": "Set for ventral and incisional hernia repair, not complex abdominal wall repair",
    "lobectomy_transoral": "Carried over from transoral robotic surgery; lobectomy not separately considered",
    "gyn_oncology": "Carried over from hysterectomy (benign and malignant); oncology-specific evidence not reviewed",
}


def _fmt(v, unit):
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, str):
        return v
    if unit.startswith("proportion") or unit == "share":
        return f"{v:.1%}" if v and v < 0.1 else f"{v:.0%}"
    if unit.startswith("£"):
        return f"£{v:,.0f}"
    return f"{v:g}"


def _p_open_source(k):
    if k in ("colectomy", "rectal"):
        return SRC["nboca"] + " (25% of major bowel cancer resections open, 2023)", \
            "National audit (population, not the robotic subgroup)", "Context only"
    if k in ("benign_gyn", "gyn_oncology"):
        return SRC["hyst"], "National data (population, not the robotic subgroup)", "Context only"
    if k == "abdo_wall_repair":
        return SRC["hernia"], "National data (population, not the robotic subgroup)", "Context only"
    if k == "prostatectomy":
        return SRC["nice"] + " (robotic prostatectomy is established practice); open is the default comparator", \
            "Policy context", "Placeholder"
    return "None found (placeholder)", "None", "Placeholder"


def _effect_source(k, g, field):
    if not g.get("benefit_modelled", True) and not field.startswith("extra_minutes"):
        src, grade = NEW_EVIDENCE.get(k, ("No evidence reviewed", "None"))
        return "Evidence for review: " + src, grade, "Not yet modelled"
    if k == "colectomy" and field == "conv_reduction_lap":
        return SRC["surg_endosc_2024"], "Observational (national registry)", "Sourced"
    if k == "colectomy" and field == "los_reduction_lap":
        return SRC["plos_2015"] + "; 0.5 days used", "Meta-analysis (mostly observational)", "Partly sourced"
    if k == "inguinal" and field == "extra_minutes_lap":
        return ("Evidence for review: " + SRC["rival"] + ": median 75.5 v 40.5 minutes; 0 used (placeholder)",
                "Randomised trial", "Placeholder")
    if k in FLAGGED_CARRY:
        return FLAGGED_CARRY[k], "None", "Flagged for review"
    if k == "benign_gyn":
        return "Averaged from the hysterectomy, myomectomy and endometriosis placeholders (by demand)", "None", \
            "Placeholder"
    return "Expert estimate (placeholder)", "None", "Placeholder"


def detail_rows(cfg):
    """One row per procedure and assumption, with a stable ID (see register_xlsx)."""
    out = []

    def add(id_, specialty, procedure, assumption, raw, unit, source, grade, status, owner):
        out.append(dict(id=id_, specialty=specialty, procedure=procedure, assumption=assumption, raw=raw,
                        value=_fmt(raw, unit), unit=unit, source=source, grade=grade, status=status, owner=owner))

    for k in sorted(cfg["groups"], key=lambda x: cfg["groups"][x]["label"].lower()):
        g = cfg["groups"][k]
        sp, lab = g["specialty"], g["label"]
        owner = f"[{sp} clinical benefit owner]"
        origin = g.get("origin", "")
        for size in ("medium", "large"):
            add(f"{k}.demand_{size}", sp, lab, f"Annual demand, {'medium DGH' if size == 'medium' else 'large hospital'}",
                float(g[f"cases_{size}"]), "cases a year", "Placeholder for review. " + origin, "None",
                "Placeholder", owner)
        add(f"{k}.complexity", sp, lab, "Complexity", g["complexity"], "High / Medium / Low", SRC["aneel"],
            "Clinical lead", "Clinical lead input", owner)
        add(f"{k}.whole_day", sp, lab, "Whole-day procedure (one case across two sessions)", bool(g.get("whole_day")),
            "yes / no", "Project proposal approved October 2026 (cystectomy, pancreatoduodenectomy, oesophagogastric "
            "and liver resection)", "None", "Assumption", owner)
        add(f"{k}.cases_per_session", sp, lab, "Cases per session", float(g["cases_per_session"]), "cases",
            "Default from complexity (High 1, Medium 1.5, Low 3; whole day 0.5). No published operating-time source "
            "used", "None", "Assumption", owner)
        if E.is_multi_comparator(g):
            for c, v in g["comparators"].items():
                add(f"{k}.share.{c}", sp, lab, f"Share that would have {D.COMPARATOR_LABELS[c].lower()} without the "
                    "robot", float(v), "share", g.get("evidence_note", ""), "Early series", "Placeholder", owner)
                for m in D.SP_REDUCTION_KEYS:
                    add(f"{k}.{c}.{m}", sp, lab, f"{D.FIELD_LABELS[m].capitalize()} v {D.COMPARATOR_SHORT[c].lower()}",
                        float(g["reductions"][c][m]), "days per case" if m == "los" else "proportion per case",
                        g.get("evidence_note", ""), "Early series", "Placeholder", owner)
                add(f"{k}.{c}.extra_minutes", sp, lab, f"Extra theatre minutes v {D.COMPARATOR_SHORT[c].lower()}",
                    float(g["extra_minutes"][c]), "minutes per case", "Placeholder", "None", "Placeholder", owner)
        else:
            src, grade, status = _p_open_source(k)
            add(f"{k}.p_open", sp, lab, "Share that would be open without the robot", float(g["p_open"]), "share",
                src, grade, status, owner)
            for field, name, unit in EFFECTS:
                src, grade, status = _effect_source(k, g, field)
                add(f"{k}.{field}", sp, lab, name, float(g[field]), unit, src, grade, status, owner)
        add(f"{k}.tariff_uplift", sp, lab, "Extra tariff income per robotic case (cash case only)",
            float(g.get("tariff_uplift", 0.0)), "£ per case",
            D.TARIFF_SOURCES.get(k.replace("sp_", ""), D.DEFAULT_TARIFF_SOURCE),
            "Policy (NHS Payment Scheme)" if k.replace("sp_", "") in D.TARIFF_SOURCES else "None", "Placeholder",
            "[Finance lead]")

    uc, pr = cfg["unit_costs"], cfg["programme"]
    fin, sro = "[Finance lead]", "[Senior responsible owner]"
    allp = "All procedures"
    add("unit_costs.bed_day", "All", allp, "Excess bed-day (cost avoided, not cash)", float(uc["bed_day"]), "£",
        f"Single-trust FOI 2023/24 (£379); national context: {SRC['pq']}", "Local, single trust", "Placeholder", fin)
    for key in ("reoperation", "major_complication", "readmission", "conversion", "theatre_minute",
                "decontamination_per_case"):
        add(f"unit_costs.{key}", "All", allp, D.UNIT_COST_LABELS[key], float(uc[key]), "£", "None found", "None",
            "Placeholder", fin)
    for key, name, unit, src, status in [
            ("realisation_factor", "Share of templated cases that go ahead", "share",
             "None found (cancellations and under-runs)", "Placeholder"),
            ("operating_weeks_per_year", "Operating weeks per year", "weeks", "None found", "Assumption"),
            ("implementation_cost_per_robot", "Implementation, training and proctoring per robot", "£",
             "None found; GIRFT 2025 asks the business case to consider proctoring arrangements", "Placeholder"),
            ("theatre_modification_per_robot", "Theatre works per robot (one-off)", "£", "None found", "Placeholder"),
            ("sfa_wte_per_robot", "Surgical first assistant: WTE per robot", "WTE", SRC["girft"], "Partly sourced"),
            ("sfa_cost_per_wte", "Surgical first assistant: cost per WTE", "£", "None found (placeholder)",
             "Placeholder"),
            ("max_cases_per_robot", "Cases per robot per year: advisory level", "cases",
             "Project team decision (amber guardrail, not a cut)", "Assumption"),
            ("discount_rate", "Discount rate (economic case)", "share", SRC["green"], "Sourced"),
            ("pdc_rate", "Public dividend capital", "share", "DHSC policy rate", "Sourced")]:
        add(f"programme.{key}", "All", allp, name, float(pr[key]), unit, src,
            "Policy" if status == "Sourced" else "None", status, sro if key != "pdc_rate" else fin)
    return out


def rows(cfg):
    """Compact register for the Word business case and the website."""
    out = []

    def add(param, value, source, grade, status, owner):
        out.append(dict(parameter=param, value=value, source=source, grade=grade, status=status, owner=owner))

    det = {r["id"]: r for r in detail_rows(cfg)}
    for k, g in cfg["groups"].items():
        if not g["volume"]:
            continue
        owner = f"[{g['specialty']} clinical benefit owner]"
        add(f"{g['label']}: annual demand", f"{g['volume']:,.0f}", "Placeholder for review. " + g.get("origin", ""),
            "None", "Placeholder", owner)
        add(f"{g['label']}: complexity and cases per session",
            f"{g['complexity']}; {g['cases_per_session']:g} per session" + (" (whole day)" if g.get("whole_day") else ""),
            SRC["aneel"] + "; cases per session from the approved complexity defaults", "Clinical lead",
            "Clinical lead input", owner)
        if E.is_multi_comparator(g):
            mix = ", ".join(f"{D.COMPARATOR_SHORT[c].lower()} {v:.0%}" for c, v in g["comparators"].items())
            add(f"{g['label']}: what patients would have without the robot", mix,
                g.get("evidence_note", D.DEFAULT_EVIDENCE_NOTE), "Early series", "Placeholder", owner)
            add(f"{g['label']}: 30-day differences", "See Appendix A", g.get("evidence_note", ""), "Early series",
                "Flagged for review" if "merged" in g.get("evidence_note", "") else "Placeholder", owner)
            continue
        po = det[f"{k}.p_open"]
        add(f"{g['label']}: share that would be open without the robot", po["value"], po["source"], po["grade"],
            po["status"], owner)
        if not g.get("benefit_modelled", True):
            src, grade = NEW_EVIDENCE.get(k, ("No evidence reviewed", "None"))
            add(f"{g['label']}: 30-day differences", "Not yet modelled (zero placeholder)",
                "Evidence for review: " + src, grade, "Not yet modelled", owner)
        else:
            src, grade, status = _effect_source(k, g, "los_reduction_open")
            if k == "colectomy":
                src, grade, status = (f"{SRC['surg_endosc_2024']}; {SRC['plos_2015']}", "Observational and "
                                      "meta-analysis", "Partly sourced")
            add(f"{g['label']}: 30-day differences (bed-days, events, theatre time)", "See Appendix A", src, grade,
                status, owner)
        if k in D.TARIFF_SOURCES:
            val = g.get("tariff_uplift", 0.0)
            add(f"{g['label']}: extra tariff income per case", f"£{val:,.0f}", D.TARIFF_SOURCES[k],
                "Policy (NHS Payment Scheme)", "Placeholder" if val == 0 else "Trust input", "[Finance lead]")

    pf, pr, uc = cfg["platform"], cfg["programme"], cfg["unit_costs"]
    if cfg.get("template") is not None:
        add("Two-week theatre template", {"standard": "Standard day, pre-filled from demand",
                                          "extended": "Extended day, pre-filled from demand"}.get(
            cfg.get("template_variant"), "Entered by the trust"),
            "Trust theatre plan", "Local", "Trust input", "[Theatres lead]")
    add("Cases per session by complexity", "High 1, Medium 1.5, Low 3; whole day 0.5",
        "Project proposal approved October 2026; no published operating-time source used", "None", "Assumption",
        "[Clinical lead]")
    add("Share of templated cases that go ahead", f"{pr.get('realisation_factor', 1.0):.0%}",
        "None found (cancellations and under-runs)", "None", "Placeholder", "[Theatres lead]")
    add("Extra tariff income, all other procedures", "£0", D.DEFAULT_TARIFF_SOURCE + " Not checked per HRG.",
        "None", "Placeholder", "[Finance lead]")
    add("Tariff: patients would otherwise be treated at this trust", "Assumed",
        "If they would otherwise go to another provider, the trust gains the whole tariff and that provider "
        "loses it: a transfer, not a gain to the NHS", "n/a", "Assumption", "[Finance lead]")
    add("Tariff: payment mechanism and market forces factor", "Not modelled",
        "Elective income may be paid under aligned payment and incentive (fixed plus variable) rather than full "
        "unit prices; the market forces factor is not applied", "n/a", "Placeholder", "[Finance lead]")

    # Unit costs ---------------------------------------------------------------
    fin = "[Finance lead]"
    add("Excess bed-day (cost avoided, not cash)", f"£{uc['bed_day']:,.0f}",
        f"Single-trust FOI 2023/24 (£379); national context: {SRC['pq']}", "Local, single trust",
        "Placeholder", fin)
    for key in ("reoperation", "major_complication", "readmission", "conversion"):
        add(D.UNIT_COST_LABELS[key], f"£{uc[key]:,.0f}", "None found", "None", "Placeholder", fin)
    add("Extra theatre minute", f"£{uc['theatre_minute']:,.0f}", "None found", "None", "Placeholder", fin)
    add("Sterile services per robotic case", f"£{uc.get('decontamination_per_case', 0):,.0f}",
        "None found; sterilisation requirements are listed for consideration in system choice (GIRFT 2025)", "None", "Placeholder", fin)

    # Platform and commercial ------------------------------------------------------
    proc = "[Procurement lead]"
    add("Platform price basis", pf["label"], pf["source"],
        "Illustrative" if pf.get("illustrative") else "Published NHS anchor (to be re-confirmed)",
        "Placeholder" if pf.get("illustrative") else "Partly sourced", proc)
    add("Instrument price per case", f"£{pf.get('instruments_per_case', 0):,.0f}",
        "US single-centre average about $1,500 per case; single-port extra $1,170 to $1,820 (" + SRC["aua"] + ")",
        "International", "Placeholder", proc)
    add("Instrument discounts (15% standard, 30% volume)", "15% and 30%", "None found", "None", "Placeholder", proc)
    if pf["model"] in ("managed_service", "per_procedure"):
        add("Contract volumes apply", D.CONTRACT_BASIS_LABELS[pf.get("contract_volume_basis", "per_robot")],
            "Contract terms", "Local", "Trust input", proc)

    # Programme ---------------------------------------------------------------------
    sro = "[Senior responsible owner]"
    add("Sessions per robot per week; operating weeks", f"{pr['sessions_per_robot_per_week']}; "
        f"{pr['operating_weeks_per_year']}", "Programmes should be fully used on all working days (GIRFT 2025)",
        "Policy", "Assumption", sro)
    add("Utilisation ramp (years 1 to 5)", ", ".join(f"{u:.0%}" for u in pr["utilisation_by_year"]),
        "None found", "None", "Assumption", sro)
    add("Learning curve on benefits (years 1 to 5)", ", ".join(f"{u:.0%}" for u in pr["learning_benefit_by_year"]),
        "None found", "None", "Assumption", sro)
    add("Implementation, training and proctoring per robot", f"£{pr['implementation_cost_per_robot']:,.0f}",
        "None found; GIRFT 2025 asks the business case to consider proctoring arrangements, including funding", "None", "Placeholder", sro)
    add("Theatre works per robot (one-off)", f"£{pr.get('theatre_modification_per_robot', 0):,.0f}",
        "None found", "None", "Placeholder", "[Estates lead]")
    add("Surgical first assistant or care practitioner", f"{pr.get('sfa_wte_per_robot', 0):g} WTE per robot at "
        f"£{pr.get('sfa_cost_per_wte', 0):,.0f}", SRC["girft"] + " (provision should be built into the business case); cost is a placeholder",
        "Guidance / none (cost)", "Partly sourced", "[Theatres lead]")
    add("Robotic cases per robot per year: advisory level", f"{pr.get('max_cases_per_robot', 700):,}",
        "Project team decision (amber guardrail above this level, not a cut)", "n/a", "Assumption", "[Project team]")
    add("Minimum list fill", f"{pr.get('min_list_fill', 0.75):.0%}",
        "Project team decision (matches the utilisation guardrail)", "n/a", "Assumption", "[Project team]")
    add("Benchmark programme volume", f"{D.BENCHMARK['cases_per_robot']} cases per robot per year",
        D.BENCHMARK["sources"]["cases_per_robot"], "Assumption with national context", "Assumption", "[Project team]")
    add("Discount rate (economic case)", f"{pr['discount_rate']:.1%}", SRC["green"], "Policy", "Sourced", fin)
    add("Public dividend capital", f"{pr['pdc_rate']:.1%}", "DHSC policy rate", "Policy", "Sourced", fin)
    return out


def summary(cfg):
    from collections import Counter
    return dict(Counter(r["status"] for r in rows(cfg)))
