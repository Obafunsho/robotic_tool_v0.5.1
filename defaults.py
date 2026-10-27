"""
Default placeholder inputs for the robotic programme decision engine.

EVERY value here is a placeholder for expert review. None is drawn from a
locked evidence synthesis. Users overwrite any value; the engine flags
any benefit prior that differs from these defaults as "user-modified".

Sign convention (deliberately clinician-friendly):
  *_reduction  : positive number = benefit of robotic over comparator
                 (e.g. los_reduction_open = 2.0 means 2 fewer bed-days)
  extra_minutes: positive number = robotic case takes longer
All absolute event values are proportions per case (0.02 = 2 percentage points).

Anti-double-counting rule:
  los_reduction_* is the TOTAL difference in mean index length of stay,
  including stay caused by complications. Event unit costs below are
  therefore NON-WARD costs only (theatre, critical care, intervention),
  except readmission, which is a separate spell and is costed in full.
"""

ENGINE_VERSION = "0.5.1"

# ---------------------------------------------------------------------------
# Procedure groups
# cases_medium / cases_large : placeholder ANNUAL ROBOTIC CASES available to the
#                              robot (one step: no separate "suitable" fraction)
# p_open                     : counterfactual share. Of these robotic cases, the
#                              proportion that would be OPEN if the trust had no
#                              robot (the rest laparoscopic).
# p_robot_elsewhere          : share that would have robotic surgery at another
#                              centre (no 30-day difference). Default 0; used for
#                              the prostatectomy sensitivity scenario.
# cases_per_list             : cases on one list
# list_sessions              : 1 = half-day list, 2 = all-day list
#                              (colorectal 2 cases per all-day list; set 3 to test
#                              a high-throughput list, which needs the cases to fill it)
# nhse_priority              : NHSE-signalled specialty (allocation priority)
# ---------------------------------------------------------------------------
def _g(label, specialty, cases_medium, cases_large, p_open, cases_per_list,
       list_sessions, nhse_priority, rationale, **b):
    return dict(label=label, specialty=specialty, cases_medium=cases_medium,
                cases_large=cases_large, p_open=p_open, cases_per_list=cases_per_list,
                list_sessions=list_sessions, nhse_priority=nhse_priority,
                p_open_rationale=rationale, p_robot_elsewhere=0.0, **b)


PROCEDURE_GROUPS = {
    "colorectal": _g(
        "Colorectal major resection (colon and rectum)", "Colorectal", 120, 200,
        0.10, 2, 2, False,
        "Most suitable cases are already laparoscopic; robot displaces some open (e.g. obese, pelvic, re-do).",
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.05,
        reop_reduction_open=0.02, reop_reduction_lap=0.005,
        comp_reduction_open=0.04, comp_reduction_lap=0.005,
        readm_reduction_open=0.01, readm_reduction_lap=0.0,
        extra_minutes_open=30, extra_minutes_lap=20),
    "prostatectomy": _g(
        "Radical prostatectomy", "Urology", 0, 250,
        1.00, 3, 2, False,
        "Comparator is open surgery. Robotic prostatectomy is established NHS practice, so robotic care at another centre is shown as a sensitivity scenario.",
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.02,
        reop_reduction_open=0.005, reop_reduction_lap=0.0,
        comp_reduction_open=0.02, comp_reduction_lap=0.005,
        readm_reduction_open=0.005, readm_reduction_lap=0.0,
        extra_minutes_open=0, extra_minutes_lap=0),
    "nephrectomy": _g(
        "Nephrectomy and partial nephrectomy", "Urology", 50, 120,
        0.30, 3, 2, False,
        "Partial nephrectomy is often open without a robot; radical mostly laparoscopic.",
        los_reduction_open=2.0, los_reduction_lap=0.3, conv_reduction_lap=0.03,
        reop_reduction_open=0.005, reop_reduction_lap=0.0,
        comp_reduction_open=0.03, comp_reduction_lap=0.005,
        readm_reduction_open=0.005, readm_reduction_lap=0.0,
        extra_minutes_open=20, extra_minutes_lap=15),
    "cystectomy": _g(
        "Radical cystectomy", "Urology", 0, 50,
        0.80, 1, 2, False,
        "Largely open without a robot.",
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.03,
        reop_reduction_open=0.01, reop_reduction_lap=0.0,
        comp_reduction_open=0.03, comp_reduction_lap=0.01,
        readm_reduction_open=0.0, readm_reduction_lap=0.0,
        extra_minutes_open=60, extra_minutes_lap=20),
    "hysterectomy": _g(
        "Hysterectomy (benign and malignant)", "Gynaecology", 100, 160,
        0.50, 2, 1, True,
        "Complex cases offered to the robot (large uterus, obesity) are often open otherwise.",
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.03,
        reop_reduction_open=0.005, reop_reduction_lap=0.0,
        comp_reduction_open=0.03, comp_reduction_lap=0.005,
        readm_reduction_open=0.005, readm_reduction_lap=0.0,
        extra_minutes_open=20, extra_minutes_lap=20),
    "myomectomy": _g(
        "Myomectomy", "Gynaecology", 25, 40,
        0.80, 1, 1, True,
        "Predominantly open without a robot.",
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.05,
        reop_reduction_open=0.0, reop_reduction_lap=0.0,
        comp_reduction_open=0.03, comp_reduction_lap=0.005,
        readm_reduction_open=0.005, readm_reduction_lap=0.0,
        extra_minutes_open=30, extra_minutes_lap=20),
    "endometriosis": _g(
        "Endometriosis excision", "Gynaecology", 40, 60,
        0.20, 2, 2, True,
        "Mostly laparoscopic; deep disease with bowel involvement sometimes open.",
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.03,
        reop_reduction_open=0.005, reop_reduction_lap=0.0,
        comp_reduction_open=0.02, comp_reduction_lap=0.005,
        readm_reduction_open=0.005, readm_reduction_lap=0.0,
        extra_minutes_open=20, extra_minutes_lap=20),
    "adnexal": _g(
        "Adnexal surgery", "Gynaecology", 30, 50,
        0.10, 3, 1, True,
        "Mostly laparoscopic; low value on the robot except complex masses.",
        los_reduction_open=1.0, los_reduction_lap=0.0, conv_reduction_lap=0.01,
        reop_reduction_open=0.0, reop_reduction_lap=0.0,
        comp_reduction_open=0.01, comp_reduction_lap=0.0,
        readm_reduction_open=0.0, readm_reduction_lap=0.0,
        extra_minutes_open=10, extra_minutes_lap=15),
    "abdominal_wall": _g(
        "Abdominal wall (ventral and incisional hernia)", "General surgery", 80, 120,
        0.70, 2, 1, True,
        "Most ventral and incisional repairs are open without a robot.",
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.02,
        reop_reduction_open=0.005, reop_reduction_lap=0.0,
        comp_reduction_open=0.03, comp_reduction_lap=0.005,
        readm_reduction_open=0.01, readm_reduction_lap=0.0,
        extra_minutes_open=45, extra_minutes_lap=30),
    "paediatric": _g(
        "Paediatric (e.g. pyeloplasty, fundoplication)", "Paediatric surgery", 0, 50,
        0.50, 2, 1, True,
        "Mixed open and laparoscopic without a robot.",
        los_reduction_open=1.0, los_reduction_lap=0.2, conv_reduction_lap=0.02,
        reop_reduction_open=0.0, reop_reduction_lap=0.0,
        comp_reduction_open=0.01, comp_reduction_lap=0.0,
        readm_reduction_open=0.0, readm_reduction_lap=0.0,
        extra_minutes_open=30, extra_minutes_lap=20),
    "head_neck": _g(
        "Head and neck (transoral robotic surgery)", "Head and neck", 0, 40,
        0.80, 3, 2, False,
        "Counterfactual is open access surgery; non-surgical treatment is not modelled.",
        los_reduction_open=3.0, los_reduction_lap=0.0, conv_reduction_lap=0.0,
        reop_reduction_open=0.01, reop_reduction_lap=0.0,
        comp_reduction_open=0.05, comp_reduction_lap=0.0,
        readm_reduction_open=0.01, readm_reduction_lap=0.0,
        extra_minutes_open=30, extra_minutes_lap=0),
    "upper_gi": _g(
        "Upper GI (anti-reflux and hiatal hernia)", "Upper GI", 20, 40,
        0.05, 2, 1, False,
        "Almost all laparoscopic without a robot.",
        los_reduction_open=2.0, los_reduction_lap=0.2, conv_reduction_lap=0.02,
        reop_reduction_open=0.005, reop_reduction_lap=0.0,
        comp_reduction_open=0.02, comp_reduction_lap=0.005,
        readm_reduction_open=0.0, readm_reduction_lap=0.0,
        extra_minutes_open=30, extra_minutes_lap=20),
}

BENEFIT_KEYS = [
    "los_reduction_open", "los_reduction_lap", "conv_reduction_lap",
    "reop_reduction_open", "reop_reduction_lap",
    "comp_reduction_open", "comp_reduction_lap",
    "readm_reduction_open", "readm_reduction_lap",
]

# Evidence settings: multiplier applied to every benefit reduction.
# Extra theatre minutes are NOT scaled (kept conservative against the robot).
# Evidence notes shown in the business case appendix. Supplier names are never used.
EVIDENCE_NOTES = {
    "colorectal": ("Versus laparoscopy: conversion 9.8% v 4.8% in elective colectomy for cancer (US national registry, "
                   "Surg Endosc 2024); length of stay mean difference -0.68 days (meta-analysis, PLoS One 2015). "
                   "Open share is a placeholder: 25% of major bowel cancer resections in England and Wales were open "
                   "in 2023 (NBOCA 2025), and patients chosen for the robot are a selected subgroup. Versus open: expert estimate."),
    "prostatectomy": ("Excluded from NICE's 2025 early value assessment because robotic prostatectomy is established "
                      "NHS practice. Effect sizes versus open are placeholders."),
    "hysterectomy": ("Open share placeholder. In England, about half of hysterectomies were laparoscopic by 2011-17 "
                     "(Madhvani et al, cited in Clark and Saridogan 2021). Effect sizes are placeholders."),
    "abdominal_wall": ("Open share placeholder. Open repair remains the commonest approach to hernia repair in UK "
                       "national data (World J Emerg Surg 2025). Effect sizes are placeholders."),
    "bed_day": ("Excess ward bed-day placeholder (single-trust FOI, 2023/24: £379 including ward costs and overheads, "
                "rounded up). The national average elective inpatient cost per bed-day was £1,198 in 2024/25, but this "
                "includes treatment costs and overstates the value of a day saved at the end of a stay. Bed-days are "
                "cost avoided, not cash released, and are not deducted from the extra cost to the trust."),
}
DEFAULT_EVIDENCE_NOTE = "Best-available estimate pending specialty review (placeholder)."

EVIDENCE_SETTINGS = {"no_benefit": 0.0, "conservative": 0.5, "central": 1.0, "optimistic": 1.5}
EVIDENCE_LABELS = {"no_benefit": "No benefit", "conservative": "Conservative (half)",
                   "central": "Central", "optimistic": "Optimistic (1.5 times)"}

# ---------------------------------------------------------------------------
# Unit costs (placeholders, 2025-26 GBP). See anti-double-counting rule above.
# ---------------------------------------------------------------------------
UNIT_COSTS = dict(
    bed_day=400,          # excess ward bed-day (cost avoided, not cash)
    reoperation=6000,     # non-ward cost of a return to theatre
    major_complication=4000,  # non-ward cost (critical care, intervention)
    readmission=2500,     # full readmission spell
    conversion=1000,      # non-ward cost of converting lap to open
    theatre_minute=12,    # cost per extra theatre minute (included: conservative)
    decontamination_per_case=75,  # sterile services reprocessing of robotic instruments (placeholder)
)

# ---------------------------------------------------------------------------
# Platforms (generic: no supplier is named) and procurement models
# model: "purchase" | "lease" | "managed_service" | "per_procedure"
# contract_volume_basis: "per_robot" (default) or "per_contract". Applies to
#   cases included (managed service) and minimum cases (per-procedure fee).
# ---------------------------------------------------------------------------
PLATFORMS = {
    "platform_a": dict(
        label="Platform A: next-generation multi-port (purchase)", model="purchase",
        capital=2_200_000, trade_in=0, asset_life_years=7,
        maintenance_per_year=170_000, instruments_per_case=1600, illustrative=False,
        source=("Platform B anchor plus about 15% like-for-like uplift reported by a manufacturer (2024); "
                "uplift not re-verified in v0.5")),
    "platform_b": dict(
        label="Platform B: established multi-port (purchase)", model="purchase",
        capital=1_920_000, trade_in=0, asset_life_years=7,
        maintenance_per_year=150_000, instruments_per_case=1500, illustrative=False,
        source=("Capital from a published NHS trust business case (May 2026; reference to be re-confirmed). "
                "Of the same order as an earlier NHS full business case (about £2 million capital and £150,000 "
                "maintenance a year). Instruments: US single-centre average about $1,500 per case")),
    "platform_c": dict(
        label="Platform C: modular (managed service)", model="managed_service",
        annual_fee=450_000, cases_included=300, excess_fee_per_case=1200,
        contract_volume_basis="per_robot",
        instruments_included=False, instruments_per_case=1200, illustrative=True,
        source="Illustrative only: no public price; enter the trust's quote"),
    "platform_d": dict(
        label="Platform D: single-port (purchase), exploratory", model="purchase",
        procedure_set="single_port", exploratory=True,
        capital=2_000_000, trade_in=0, asset_life_years=7,
        maintenance_per_year=170_000, instruments_per_case=2500, illustrative=True,
        source=("Illustrative only. Instruments set about £1,000 per case above multi-port, "
                "reflecting reported extra instrument and drape costs of $1,170 to $1,820 per case "
                "(AUA 2022); capital not published")),
    "custom_purchase": dict(
        label="Other platform (purchase, enter quote)", model="purchase",
        capital=1_500_000, trade_in=0, asset_life_years=7,
        maintenance_per_year=120_000, instruments_per_case=1200, illustrative=True,
        source="Illustrative only: enter the trust's quote"),
    "custom_lease": dict(
        label="Other platform (lease, enter quote)", model="lease",
        lease_per_year=350_000, maintenance_per_year=0, instruments_per_case=1500,
        illustrative=True, source="Illustrative only: enter the trust's quote"),
    "custom_per_procedure": dict(
        label="Other platform (per-procedure fee, enter quote)", model="per_procedure",
        fee_per_case=2500, minimum_cases_per_year=300, instruments_included=True,
        contract_volume_basis="per_robot",
        instruments_per_case=0, illustrative=True,
        source="Illustrative only: enter the trust's quote"),
}
CONTRACT_BASIS_LABELS = {"per_robot": "per robot", "per_contract": "per contract (all robots together)"}
MODEL_LABELS = {"purchase": "Purchase", "lease": "Lease", "managed_service": "Managed service",
                "per_procedure": "Per-procedure fee"}

# Instrument price setting: multiplier on the platform's instrument price per case.
# Discounts are placeholders for the trust or procurement group to set.
INSTRUMENT_PRICE_SETTINGS = {"list": 1.00, "standard_discount": 0.85, "volume_discount": 0.70}
INSTRUMENT_PRICE_LABELS = {
    "list": "Supplier list price",
    "standard_discount": "Standard discount, 15% off list",
    "volume_discount": "Volume discount, 30% off list",
    "custom": "Trust quote",
}

# Central capital injection per robot (purchase models only), GBP.
CENTRAL_CAPITAL_OPTIONS = [0, 1_000_000, 2_000_000]

# ---------------------------------------------------------------------------
# Programme settings
# ---------------------------------------------------------------------------
PROGRAMME = dict(
    sessions_per_robot_per_week=9,     # half-day sessions, after maintenance and cleaning
    operating_weeks_per_year=45,
    utilisation_by_year=[0.70, 0.90, 1.0, 1.0, 1.0],      # ramp-up
    learning_benefit_by_year=[0.75, 0.90, 1.0, 1.0, 1.0],  # learning curve on benefits
    implementation_cost_per_robot=75_000,  # one-off, year 1 (training, proctoring, set-up)
    theatre_modification_per_robot=50_000,  # one-off, year 1 (placeholder: power, data, storage)
    sfa_wte_per_robot=1.0,             # surgical first assistant or care practitioner; GIRFT 2025 says provision should be built into the business case
    sfa_cost_per_wte=60_000,           # placeholder: senior AfC band plus on-costs; use local rates
    pdc_rate=0.035,                        # public dividend capital on net book value
    discount_rate=0.035,                   # HM Treasury Green Book
    horizon_years=5,
    mean_elective_los_for_capacity=4.0,    # bed-days per extra elective case enabled
    low_utilisation_warning=0.75,
    min_list_fill=0.75,                # a list is only created if it will be at least this full
    max_cases_per_robot=700,           # hard cap on robotic cases per robot per year (inputs and break-even)
    central_capital_per_robot=0,      # 0, 1,000,000 or 2,000,000: national capital injection (purchase only)
    include_capacity_value=False,     # True: value released bed-days as extra elective activity
    target_net_cost_per_bed_day=1500,  # placeholder target used for the instrument price calculation
    contribution_per_extra_case=1500, # placeholder: income less marginal cost per extra elective case
    allocation_rule="proportional",  # or "benefit"
)

# ---------------------------------------------------------------------------
# Presets: hospital type x number of robots
# ---------------------------------------------------------------------------
PRESETS = {
    # Robots per preset may be overridden; presets set typical case volumes.
    "medium_dgh_1": dict(label="Medium DGH (<800 beds), 1 robot", volume_key="cases_medium", robots=1),
    "medium_dgh_2": dict(label="Medium DGH (<800 beds), 2 robots", volume_key="cases_medium", robots=2),
    "large_1": dict(label="Large hospital (>=800 beds), 1 robot", volume_key="cases_large", robots=1),
    "large_2": dict(label="Large hospital (>=800 beds), 2 robots", volume_key="cases_large", robots=2),
}


# ---------------------------------------------------------------------------
# Single-port procedure groups (exploratory)
#
# Different maths, same interface: each group has a counterfactual mix across
# up to three comparators (what would happen without the single-port robot)
# and 30-day reductions against EACH comparator. The engine sums over them.
#   comparators: {comparator_key: share}, shares sum to 1
#   reductions : {comparator_key: {los, conv, reop, comp, readm}}
#   extra_minutes: {comparator_key: minutes}  (negative = faster)
# ---------------------------------------------------------------------------
COMPARATOR_LABELS = {
    "open": "Open surgery",
    "robot_elsewhere": "Robotic surgery at another centre",
    "conventional_mis": "Conventional minimal access (laparoscopic, endoscopic or laser)",
    "multiport_robot": "Multi-port robot",
}
COMPARATOR_SHORT = {"open": "Open", "robot_elsewhere": "Robot elsewhere", "conventional_mis": "Conventional minimal access",
                    "multiport_robot": "Multi-port robot"}
OPEN_LIKE = {"open"}   # comparators that count as "open operations avoided"


def _sp(label, specialty, cases_medium, cases_large, comparators, reductions, extra_minutes,
        cases_per_list, list_sessions, rationale, evidence):
    return dict(label=label, specialty=specialty, cases_medium=cases_medium, cases_large=cases_large,
                comparators=comparators, reductions=reductions, extra_minutes=extra_minutes,
                cases_per_list=cases_per_list, list_sessions=list_sessions, nhse_priority=False,
                p_open_rationale=rationale, evidence_note=evidence)


def _r(los=0.0, conv=0.0, reop=0.0, comp=0.0, readm=0.0):
    return dict(los=los, conv=conv, reop=reop, comp=comp, readm=readm)


SP_GROUPS = {
    "sp_prostatectomy": _sp(
        "Single-port radical prostatectomy", "Urology", 0, 150,
        dict(multiport_robot=0.90, open=0.10),
        dict(multiport_robot=_r(los=0.5), open=_r(los=2.0, reop=0.005, comp=0.02, readm=0.005)),
        dict(multiport_robot=-15, open=0), 3, 2,
        "Without a single-port robot, most would have multi-port robotic surgery.",
        "Versus multi-port: shorter stay and more same-day discharge, no difference in 30-day "
        "complications (umbrella review, J Robot Surg 2026; NSQIP analysis, World J Urol 2026). "
        "Theatre time difference is a placeholder."),
    "sp_kidney": _sp(
        "Single-port kidney surgery (partial nephrectomy, pyeloplasty)", "Urology", 0, 60,
        dict(multiport_robot=0.60, open=0.30, conventional_mis=0.10),
        dict(multiport_robot=_r(los=0.5), open=_r(los=2.0, reop=0.005, comp=0.03, readm=0.005),
             conventional_mis=_r(los=0.3, conv=0.03, comp=0.005)),
        dict(multiport_robot=0, open=20, conventional_mis=15), 3, 2,
        "Mixed: multi-port robot where available, otherwise open partial nephrectomy.",
        "Same-day discharge 83% v 17% after partial nephrectomy in one single-surgeon series "
        "(Urology 2021); otherwise placeholders."),
    "sp_transoral": _sp(
        "Single-port transoral surgery (head and neck)", "Head and neck", 0, 40,
        dict(conventional_mis=0.60, multiport_robot=0.10, open=0.30),
        dict(conventional_mis=_r(los=0.5, comp=0.01), multiport_robot=_r(los=0.3),
             open=_r(los=3.0, reop=0.01, comp=0.05, readm=0.01)),
        dict(conventional_mis=20, multiport_robot=0, open=30), 3, 2,
        "Counterfactual is transoral laser or multi-port TORS, or open access; non-surgical treatment not modelled.",
        "CE marked for transoral surgery January 2024; prospective series of 47 patients with no "
        "conversions. Effect sizes are best-available estimates."),
    "sp_transanal": _sp(
        "Single-port transanal surgery (local excision of rectal lesions)", "Colorectal", 30, 50,
        dict(conventional_mis=0.80, open=0.20),
        dict(conventional_mis=_r(los=0.2, comp=0.01), open=_r(los=0.5, reop=0.005, comp=0.02)),
        dict(conventional_mis=20, open=30), 2, 1,
        "Without the robot, most would have conventional transanal endoscopic surgery; some open transanal excision.",
        "Feasibility series and preclinical work only; effect sizes are best-available estimates."),
    "sp_thoracic": _sp(
        "Single-port thoracic surgery (lung and mediastinal resection)", "Thoracic", 0, 40,
        dict(conventional_mis=0.80, open=0.20),
        dict(conventional_mis=_r(los=0.3, conv=0.01), open=_r(los=2.5, reop=0.005, comp=0.05, readm=0.01)),
        dict(conventional_mis=20, open=0), 2, 2,
        "Most would have video-assisted thoracoscopic surgery; some open thoracotomy.",
        "Early international series only; effect sizes are best-available estimates."),
}
SP_REDUCTION_KEYS = ["los", "conv", "reop", "comp", "readm"]


# ---------------------------------------------------------------------------
# Benchmark profile: a well-functioning multi-port programme, shown side by
# side with the trust's proposal. Each value carries its source; anything
# without a published source is labelled as an assumption, not estimated.
# ---------------------------------------------------------------------------
BENCHMARK = dict(
    label="Benchmark: well-functioning programme (1 robot)",
    robots=1,
    cases_per_robot=550,
    platform="platform_b",
    instrument_price="standard_discount",
    central_capital_per_robot=None,   # None = same capital source as the trust's case
    # specialty shares of robotic activity (urology, general surgery, gynaecology),
    # renormalised from the three specialties that made up 90% of UK NHS robotic
    # procedures in 2024 (43.2%, 29.6%, 16.8%)
    specialty_shares={"Urology": 43.2, "General surgery": 29.6, "Gynaecology": 16.8},
    # split within each specialty: assumption (no published split found)
    within_specialty={
        "Urology": {"prostatectomy": 0.60, "nephrectomy": 0.30, "cystectomy": 0.10},
        "General surgery": {"colorectal": 0.70, "abdominal_wall": 0.20, "upper_gi": 0.10},
        "Gynaecology": {"hysterectomy": 0.60, "endometriosis": 0.20, "myomectomy": 0.10, "adnexal": 0.10},
    },
    sources=dict(
        cases_per_robot=("Assumption set by the project team. No published per-robot benchmark was found. For context, "
                         "UK NHS trusts reported 36,209 robotic procedures on 212 systems in 2024 (about 171 per "
                         "system). That study grouped trusts by annual volume, with 500 to 750 procedures a year as "
                         "its high-volume category (Donald et al, Surg Endosc 2026)."),
        specialty_shares=("Donald et al, Surg Endosc 2026: urology, general surgery and gynaecology made up 90% of UK NHS "
                          "robotic procedures in 2024 (43.2%, 29.6%, 16.8%); the benchmark renormalises these three "
                          "to 100% and excludes other specialties."),
        within_specialty="Assumption (no published split by procedure found).",
        platform=("Platform B capital and maintenance, instruments at the standard discount (mid-level costs); "
                  "same capital source as this proposal."),
        clinical="Same 30-day assumptions as the trust's case (Appendix A).",
    ),
)

# Human-readable labels for assumption fields (used in every output; no internal keys)
FIELD_LABELS = {
    "p_open": "share open without the robot",
    "p_robot_elsewhere": "share robotic at another centre without the robot",
    "cases_per_list": "cases per list",
    "los_reduction_open": "bed-days saved versus open",
    "los_reduction_lap": "bed-days saved versus laparoscopic",
    "conv_reduction_lap": "conversions avoided versus laparoscopic",
    "reop_reduction_open": "returns to theatre avoided versus open",
    "reop_reduction_lap": "returns to theatre avoided versus laparoscopic",
    "comp_reduction_open": "major complications avoided versus open",
    "comp_reduction_lap": "major complications avoided versus laparoscopic",
    "readm_reduction_open": "readmissions avoided versus open",
    "readm_reduction_lap": "readmissions avoided versus laparoscopic",
    "extra_minutes_open": "extra theatre minutes versus open",
    "extra_minutes_lap": "extra theatre minutes versus laparoscopic",
    "los": "bed-days saved", "conv": "conversions avoided", "reop": "returns to theatre avoided",
    "comp": "major complications avoided", "readm": "readmissions avoided",
    "extra_minutes": "extra theatre minutes", "share": "share",
}
UNIT_COST_LABELS = {
    "bed_day": "Excess bed-day", "reoperation": "Return to theatre (non-ward)",
    "major_complication": "Major complication (non-ward)", "readmission": "Readmission (full spell)",
    "conversion": "Conversion to open (non-ward)", "theatre_minute": "Extra theatre minute",
    "decontamination_per_case": "Sterile services per robotic case",
}
