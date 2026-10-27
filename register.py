"""
Assumptions register: every input the business case depends on, with the value
used, its source, an evidence grade, its status and who must sign it off.

Status values
  Sourced      : taken from a cited publication or policy document
  Context only : a source gives national context but not the value itself
  Placeholder  : no adequate source yet; must be replaced or confirmed locally
  Assumption   : a modelling choice made by the project team
  Trust input  : entered by the trust; to be evidenced locally
Nothing in the register is marked as reviewed: specialty review is pending.
"""
import defaults as D
import engine as E

REVIEW = "Awaiting specialty review"

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
    sp_umbrella="Kishore et al, J Robot Surg 2026; Wallace et al, World J Urol 2026",
)


def rows(cfg):
    pf, pr, uc = cfg["platform"], cfg["programme"], cfg["unit_costs"]
    out = []

    def add(param, value, source, grade, status, owner):
        out.append(dict(parameter=param, value=value, source=source, grade=grade, status=status, owner=owner))

    # Clinical assumptions by specialty --------------------------------------
    for k, g in cfg["groups"].items():
        if not g["volume"]:
            continue
        owner = f"[{g['specialty']} clinical benefit owner]"
        add(f"{g['label']}: robotic cases per year", f"{g['volume']:,.0f}", "Trust activity data",
            "Local", "Trust input", owner)
        if E.is_multi_comparator(g):
            mix = ", ".join(f"{D.COMPARATOR_SHORT[c].lower()} {v:.0%}" for c, v in g["comparators"].items())
            add(f"{g['label']}: what patients would have without the robot", mix,
                g.get("evidence_note", D.DEFAULT_EVIDENCE_NOTE), "Low (early series)", "Placeholder", owner)
            add(f"{g['label']}: 30-day differences", "See Appendix A", g.get("evidence_note", ""),
                "Low (early series)", "Placeholder", owner)
            continue
        src = {"colorectal": SRC["nboca"], "hysterectomy": SRC["hyst"], "abdominal_wall": SRC["hernia"],
               "prostatectomy": SRC["nice"]}.get(k, "None found")
        status = "Context only" if k in ("colorectal", "hysterectomy", "abdominal_wall") else "Placeholder"
        add(f"{g['label']}: share that would be open without the robot", f"{g['p_open']:.0%}", src,
            "Indirect (population rates, not the robotic subgroup)" if status == "Context only" else "None",
            status, owner)
        eff_src = {"colorectal": f"{SRC['surg_endosc_2024']}; {SRC['plos_2015']}"}.get(k, "Expert estimate")
        add(f"{g['label']}: 30-day differences (bed-days, events, theatre time)", "See Appendix A", eff_src,
            "Observational, international" if k == "colorectal" else "None", 
            "Partly sourced" if k == "colorectal" else "Placeholder", owner)

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
    add("Maximum robotic cases per robot per year", f"{pr.get('max_cases_per_robot', 700):,}",
        "Project team decision (hard cap)", "n/a", "Assumption", "[Project team]")
    add("Minimum list fill before a list is created", f"{pr.get('min_list_fill', 0.75):.0%}",
        "Project team decision (matches the utilisation guardrail)", "n/a", "Assumption", "[Project team]")
    add("Benchmark programme volume", f"{D.BENCHMARK['cases_per_robot']} cases per robot per year",
        D.BENCHMARK["sources"]["cases_per_robot"], "Assumption with national context", "Assumption", "[Project team]")
    add("Discount rate (economic case)", f"{pr['discount_rate']:.1%}", SRC["green"], "Policy", "Sourced", fin)
    add("Public dividend capital", f"{pr['pdc_rate']:.1%}", "DHSC policy rate", "Policy", "Sourced", fin)
    return out


def summary(cfg):
    from collections import Counter
    return dict(Counter(r["status"] for r in rows(cfg)))
