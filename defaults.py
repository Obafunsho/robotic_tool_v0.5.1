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

ENGINE_VERSION = "0.7.0"

# ---------------------------------------------------------------------------
# Procedures (v0.7: Aneel's list of 17)
# cases_medium / cases_large : placeholder ANNUAL ROBOTIC CASES (demand), medium DGH / large
# complexity                 : High, Medium or Low; sets the default cases per session
# whole_day                  : True if one case takes a whole day (AM and PM sessions)
# cases_per_session          : cases per booked session (editable; flagged when changed)
# benefit_modelled           : False where the 30-day benefit is not yet modelled (zero
#                              placeholder): shown as "not yet modelled", never as no benefit
# p_open                     : of these robotic cases, the share that would be OPEN without the
#                              robot (the rest laparoscopic)
# p_robot_elsewhere          : share that would have robotic surgery at another centre (no 30-day
#                              difference); used for the prostatectomy sensitivity scenario
# tariff_uplift              : extra income per robotic case over what the trust would earn for
#                              the same patient without the robot (cash case only)
# origin                     : how the v0.6 assumptions were carried over, merged or split
# list_sessions/cases_per_list: derived, used only by the demand-led planner (template=None)
# ---------------------------------------------------------------------------
COMPLEXITY_CASES = {"High": 1.0, "Medium": 1.5, "Low": 3.0}
WHOLE_DAY_CASES = 0.5          # one case per day across two sessions
COMPLEXITY_LIST_SESSIONS = {"High": 2, "Medium": 1, "Low": 1}


def default_cases_per_session(complexity, whole_day):
    return WHOLE_DAY_CASES if whole_day else COMPLEXITY_CASES[complexity]


def _g(label, specialty, complexity, whole_day, cases_medium, cases_large, p_open, nhse_priority,
       benefit_modelled, rationale, origin, **b):
    cps = default_cases_per_session(complexity, whole_day)
    ls = COMPLEXITY_LIST_SESSIONS[complexity]
    return dict(label=label, specialty=specialty, complexity=complexity, whole_day=whole_day,
                cases_per_session=cps, cases_medium=cases_medium, cases_large=cases_large,
                p_open=p_open, list_sessions=ls, cases_per_list=cps * ls, nhse_priority=nhse_priority,
                benefit_modelled=benefit_modelled, p_open_rationale=rationale, origin=origin,
                p_robot_elsewhere=0.0, tariff_uplift=0.0, **b)


PROCEDURE_GROUPS = {
    "bariatric_antireflux": _g(
        'Bariatric and anti-reflux surgery', 'Oesophagogastric', 'Medium', False, 30, 60, 0.05, False, True,
        'Almost all laparoscopic without a robot.',
        'Carried over from upper GI (anti-reflux and hiatal hernia); bariatric surgery added. Demand placeholder raised from 20/40.',
        los_reduction_open=2.0, los_reduction_lap=0.2, conv_reduction_lap=0.02, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.02, comp_reduction_lap=0.005, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),
    "colectomy": _g(
        'Colectomy (right, left, sigmoid)', 'Colorectal', 'Medium', False, 72, 120, 0.1, False, True,
        'Most suitable cases are already laparoscopic; robot displaces some open (e.g. obese, pelvic, re-do).',
        'Carried over from colorectal major resection; colorectal demand split 60:40 colon to rectal (placeholder).',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.05, reop_reduction_open=0.02, reop_reduction_lap=0.005, comp_reduction_open=0.04, comp_reduction_lap=0.005, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),
    "abdo_wall_repair": _g(
        'Complex abdominal wall repair', 'Abdo wall complex', 'High', False, 80, 120, 0.7, True, True,
        'Most ventral and incisional repairs are open without a robot.',
        'Carried over from abdominal wall reconstruction; 30-day assumptions still those set for ventral and incisional hernia (flagged).',
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.02, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.03, comp_reduction_lap=0.005, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=45, extra_minutes_lap=30),
    "benign_gyn": _g(
        'Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy)', "Women's health", 'Medium', False, 135, 210, 0.4667, True, True,
        'Mix of hysterectomy, myomectomy and endometriosis counterfactuals, averaged by demand.',
        'Merged: benign 70% of hysterectomy (70 cases), myomectomy (25) and endometriosis (40); assumptions averaged by medium-DGH demand. Sacrocolpopexy added. Adnexal surgery dropped.',
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.0337, reop_reduction_open=0.0041, reop_reduction_lap=0.0, comp_reduction_open=0.027, comp_reduction_lap=0.005, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=21.8519, extra_minutes_lap=20.0),
    "breast": _g(
        'Complex breast (mastectomy, flap reconstruction)', 'Breast', 'Medium', False, 20, 40, 1.0, False, False,
        'Placeholder: conventional (open) mastectomy is the usual alternative.',
        'New procedure. 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "cholecystectomy": _g(
        'Complex cholecystectomy', 'Hepatopancreatobiliary', 'Medium', False, 30, 50, 0.1, False, False,
        'Placeholder: most complex cholecystectomies would otherwise be laparoscopic.',
        'New procedure. 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "inguinal": _g(
        'Complex inguinal hernia', 'Abdo wall complex', 'Low', False, 40, 60, 0.3, False, False,
        'Placeholder: complex repairs would otherwise be open or laparoscopic.',
        'New procedure: complex repairs only (recurrent, bilateral or large); standard inguinal repair stays excluded as HVLC. 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "paediatric": _g(
        'Complex paediatric (pyeloplasty, fundoplication, choledochal cyst)', 'Paediatric surgery', 'Medium', False, 0, 50, 0.5, True, True,
        'Mixed open and laparoscopic without a robot.',
        'Carried over from paediatric; choledochal cyst added.',
        los_reduction_open=1.0, los_reduction_lap=0.2, conv_reduction_lap=0.02, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.01, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),
    "gyn_oncology": _g(
        'Gynaecological oncology (radical and cancer hysterectomy)', "Women's health", 'High', False, 30, 50, 0.5, True, True,
        'Complex cases offered to the robot (large uterus, obesity) are often open otherwise.',
        'Split from hysterectomy (benign and malignant): malignant share 30% (placeholder); assumptions carried over from hysterectomy.',
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.03, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.03, comp_reduction_lap=0.005, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=20, extra_minutes_lap=20),
    "liver": _g(
        'Liver resection', 'Hepatopancreatobiliary', 'High', True, 0, 40, 0.7, False, False,
        'Placeholder: many liver resections are still open.',
        'New procedure (whole day). 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "lobectomy_transoral": _g(
        'Lobectomy and transoral surgery', 'Thoracic and head and neck', 'High', False, 0, 40, 0.8, False, True,
        'Counterfactual is open access surgery; non-surgical treatment is not modelled.',
        'Carried over from head and neck (transoral robotic surgery); lobectomy added with the same placeholder assumptions (flagged).',
        los_reduction_open=3.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.01, reop_reduction_lap=0.0, comp_reduction_open=0.05, comp_reduction_lap=0.0, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=0),
    "nephrectomy": _g(
        'Nephrectomy (partial, radical, nephroureterectomy)', 'Urology', 'Medium', False, 50, 120, 0.3, False, True,
        'Partial nephrectomy is often open without a robot; radical mostly laparoscopic.',
        'Carried over unchanged.',
        los_reduction_open=2.0, los_reduction_lap=0.3, conv_reduction_lap=0.03, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.03, comp_reduction_lap=0.005, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=20, extra_minutes_lap=15),
    "og_resection": _g(
        'Oesophagogastric resection', 'Oesophagogastric', 'High', True, 0, 30, 0.5, False, False,
        'Placeholder: many oesophagogastric resections are open or hybrid.',
        'New procedure (whole day). 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "whipple": _g(
        "Pancreatoduodenectomy (Whipple's)", 'Hepatopancreatobiliary', 'High', True, 0, 30, 0.95, False, False,
        'Placeholder: pancreatoduodenectomy is usually open.',
        'New procedure (whole day). 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "cystectomy": _g(
        'Radical cystectomy', 'Urology', 'High', True, 0, 50, 0.8, False, True,
        'Largely open without a robot.',
        'Carried over unchanged (whole day).',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.03, reop_reduction_open=0.01, reop_reduction_lap=0.0, comp_reduction_open=0.03, comp_reduction_lap=0.01, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=60, extra_minutes_lap=20),
    "prostatectomy": _g(
        'Radical prostatectomy', 'Urology', 'High', False, 0, 250, 1.0, False, True,
        'Comparator is open surgery. Robotic prostatectomy is established NHS practice, so robotic care at another centre is shown as a sensitivity scenario.',
        'Carried over unchanged. Cases per session fall from 1.5 to 1 under the complexity defaults.',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.02, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.02, comp_reduction_lap=0.005, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=0, extra_minutes_lap=0),
    "rectal": _g(
        'Rectal resection', 'Colorectal', 'High', False, 48, 80, 0.1, False, True,
        'Most suitable cases are already laparoscopic; robot displaces some open (e.g. obese, pelvic, re-do).',
        'Carried over from colorectal major resection (same placeholder assumptions, flagged); colorectal demand split 60:40 colon to rectal.',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.05, reop_reduction_open=0.02, reop_reduction_lap=0.005, comp_reduction_open=0.04, comp_reduction_lap=0.005, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),

}
NOT_YET_MODELLED_TEXT = ("30-day benefit not yet modelled: zero is a placeholder pending evidence, "
                         "not a finding that the robot has no benefit")

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
    "colectomy": ("Versus laparoscopy: conversion 9.8% v 4.8% in elective colectomy for cancer (US national registry, "
                  "Surg Endosc 2024); length of stay mean difference -0.68 days (meta-analysis, PLoS One 2015). "
                  "Open share is a placeholder: 25% of major bowel cancer resections in England and Wales were open "
                  "in 2023 (NBOCA 2025), and patients chosen for the robot are a selected subgroup. Versus open: expert estimate."),
    "rectal": ("Carried over from colorectal major resection (colon and rectum) without change; rectal-specific "
               "evidence not yet reviewed (flagged). Open share placeholder; NBOCA 2025 reports 25% of major bowel "
               "cancer resections open in 2023."),
    "prostatectomy": ("Excluded from NICE's 2025 early value assessment because robotic prostatectomy is established "
                      "NHS practice. Effect sizes versus open are placeholders."),
    "benign_gyn": ("Merged from hysterectomy, myomectomy and endometriosis (averaged by demand). In England about half of "
                   "hysterectomies were laparoscopic by 2011-17 (Madhvani et al, cited in Clark and Saridogan 2021). "
                   "Effect sizes are placeholders."),
    "gyn_oncology": "Carried over from hysterectomy (benign and malignant) without change (flagged). Placeholders.",
    "abdo_wall_repair": ("Flagged for review: the 30-day assumptions were set for ventral and incisional hernia repair, "
                         "not complex abdominal wall repair. Open share placeholder; open repair remains the commonest "
                         "approach to hernia repair in UK national data (World J Emerg Surg 2025). Versus laparoscopy, "
                         "the PROVE-IT trial found no difference in complications or length of stay for ventral hernia."),
    "breast": ("Not yet modelled (zero). Evidence for review: in a randomised trial (80 women, Ann Surg 2022) "
               "complications did not differ between robotic and open nipple-sparing mastectomy; a meta-analysis "
               "(BJS 2024) found less nipple necrosis but a longer stay after robotic surgery."),
    "cholecystectomy": ("Not yet modelled (zero). Evidence for review suggests possible harm: in US Medicare data "
                        "robotic cholecystectomy was associated with more bile duct injury than laparoscopic "
                        "(0.7% v 0.2%; instrumental variable analysis 0.4% v 0.2%; JAMA Surg 2023)."),
    "inguinal": ("Not yet modelled (zero). Evidence for review: the RIVAL randomised trial (JAMA Surg 2020) found no "
                 "30-day differences versus laparoscopic repair, with longer operations and higher cost."),
    "liver": ("Not yet modelled (zero). Evidence for review: a systematic review and meta-analysis of 2,728 robotic "
              "liver resections (2022) and matched cohorts report shorter stay and fewer complications than open "
              "resection; no randomised trial found."),
    "og_resection": ("Not yet modelled (zero). Evidence for review: the ROBOT randomised trial (Ann Surg 2019, 112 "
                     "patients) found fewer surgery-related complications after robot-assisted than open "
                     "oesophagectomy (59% v 80%)."),
    "whipple": ("Not yet modelled (zero). Evidence for review: the EUROPA randomised trial (Lancet Reg Health Eur 2024) "
                "found no difference in 90-day morbidity between robotic and open pancreatoduodenectomy, with more "
                "pancreas-specific complications and higher cost in the robotic group."),
    "lobectomy_transoral": ("Carried over from head and neck (transoral robotic surgery); lobectomy shares the same "
                            "placeholder assumptions (flagged)."),
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
    max_cases_per_session=3,          # cases per session cap on the template (adjustable)
    realisation_factor=1.0,           # share of templated cases that go ahead (cancellations): placeholder 100%
    cap_delivered_at_demand=True,     # when demand is entered, delivered cases cannot exceed it
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


def _sp(label, specialty, complexity, whole_day, cases_medium, cases_large, comparators, reductions,
        extra_minutes, rationale, evidence, origin):
    cps = default_cases_per_session(complexity, whole_day)
    ls = COMPLEXITY_LIST_SESSIONS[complexity]
    return dict(label=label, specialty=specialty, complexity=complexity, whole_day=whole_day,
                cases_per_session=cps, cases_medium=cases_medium, cases_large=cases_large,
                comparators=comparators, reductions=reductions, extra_minutes=extra_minutes,
                list_sessions=ls, cases_per_list=cps * ls, nhse_priority=False, benefit_modelled=True,
                p_open_rationale=rationale, evidence_note=evidence, origin=origin, tariff_uplift=0.0)


def _r(los=0.0, conv=0.0, reop=0.0, comp=0.0, readm=0.0):
    return dict(los=los, conv=conv, reop=reop, comp=comp, readm=readm)


# Single-port platform: restricted (v0.7) to radical prostatectomy, nephrectomy, and lobectomy
# and transoral surgery. Single-port transanal surgery is not on the list and was dropped.
SP_GROUPS = {
    "sp_prostatectomy": _sp(
        "Radical prostatectomy (single-port)", "Urology", "High", False, 0, 150,
        dict(multiport_robot=0.90, open=0.10),
        dict(multiport_robot=_r(los=0.5), open=_r(los=2.0, reop=0.005, comp=0.02, readm=0.005)),
        dict(multiport_robot=-15, open=0),
        "Without a single-port robot, most would have multi-port robotic surgery.",
        "Versus multi-port: shorter stay and more same-day discharge, no difference in 30-day "
        "complications (umbrella review, J Robot Surg 2026; NSQIP analysis, World J Urol 2026). "
        "Theatre time difference is a placeholder.",
        "Carried over unchanged."),
    "sp_nephrectomy": _sp(
        "Nephrectomy (partial, radical, nephroureterectomy) (single-port)", "Urology", "Medium", False, 0, 60,
        dict(multiport_robot=0.60, open=0.30, conventional_mis=0.10),
        dict(multiport_robot=_r(los=0.5), open=_r(los=2.0, reop=0.005, comp=0.03, readm=0.005),
             conventional_mis=_r(los=0.3, conv=0.03, comp=0.005)),
        dict(multiport_robot=0, open=20, conventional_mis=15),
        "Mixed: multi-port robot where available, otherwise open partial nephrectomy.",
        "Same-day discharge 83% v 17% after partial nephrectomy in one single-surgeon series "
        "(Urology 2021); otherwise placeholders.",
        "Carried over from single-port kidney surgery (pyeloplasty no longer listed)."),
    "sp_lobectomy_transoral": _sp(
        "Lobectomy and transoral surgery (single-port)", "Thoracic and head and neck", "High", False, 0, 80,
        dict(conventional_mis=0.7, multiport_robot=0.05, open=0.25),
        dict(conventional_mis=_r(los=0.3857, conv=0.0057, comp=0.0043), multiport_robot=_r(los=0.3), open=_r(los=2.8, reop=0.008, comp=0.05, readm=0.01)),
        dict(conventional_mis=20.0, multiport_robot=0.0, open=18.0),
        "Merged from single-port transoral and thoracic groups, weighted equally (40 and 40 cases).",
        "Early international series only; effect sizes are best-available estimates (merged, flagged).",
        "Merged from single-port transoral surgery and single-port thoracic surgery (v0.6.1)."),

}
NOT_MODELLED = set()   # v0.7: every dropdown option is a listed procedure
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
        "General surgery": {"colectomy": 0.42, "rectal": 0.28, "abdo_wall_repair": 0.20, "bariatric_antireflux": 0.10},
        "Gynaecology": {"benign_gyn": 0.80, "gyn_oncology": 0.20},
    },
    sources=dict(
        cases_per_robot=("Assumption set by the project team. No published per-robot benchmark was found. For context, "
                         "UK NHS trusts reported 36,209 robotic procedures on 212 systems in 2024 (about 171 per "
                         "system). That study grouped trusts by annual volume, with 500 to 750 procedures a year as "
                         "its high-volume category (Donald et al, Surg Endosc 2026)."),
        specialty_shares=("Donald et al, Surg Endosc 2026: urology, general surgery and gynaecology made up 90% of UK NHS "
                          "robotic procedures in 2024 (43.2%, 29.6%, 16.8%); the benchmark renormalises these three "
                          "to 100% and excludes other specialties."),
        within_specialty=("Assumption (no published split by procedure found). v0.7: colorectal split 60:40 colon "
                          "to rectal; gynaecology re-based on the v0.6 split without adnexal surgery."),
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
    "tariff_uplift": "extra tariff income per robotic case",
    "cases_per_session": "cases per session", "whole_day": "whole-day procedure",
}
UNIT_COST_LABELS = {
    "bed_day": "Excess bed-day", "reoperation": "Return to theatre (non-ward)",
    "major_complication": "Major complication (non-ward)", "readmission": "Readmission (full spell)",
    "conversion": "Conversion to open (non-ward)", "theatre_minute": "Extra theatre minute",
    "decontamination_per_case": "Sterile services per robotic case",
}


# ---------------------------------------------------------------------------
# Two-week theatre template (v0.7)
#
# Each robot has 14 days (Monday to Sunday, twice) x 3 sessions ("AM session 1",
# "PM session 2", "PM session 3"). Each session has ONE dropdown: "Unfilled session",
# a "Specialty - Procedure" option, "Maintenance" or "Closed". Cases per session come
# from the procedure's complexity (hidden from the user; editable in the advanced
# procedure table). A whole-day procedure counts half a case per session and is flagged
# if booked in only one session of a day.
#
# Standard hours are weekday sessions 1 and 2. An unfilled standard session is open but
# unbooked; an unfilled session 3 or weekend session is not in use. Friday session 2 is
# kept for maintenance by default.
# ---------------------------------------------------------------------------
SESSIONS = ["AM", "PM", "Eve"]
SESSION_LABELS = {"AM": "AM session 1", "PM": "PM session 2", "Eve": "PM session 3"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS = DAYS[:5]
UNFILLED = "Unfilled session"
SPECIAL_ENTRIES = {"": "unfilled session", "Maintenance": "not available (maintenance)",
                   "Closed": "not available"}
TEMPLATE_VARIANTS = {"standard": "Standard day (weekday AM and PM)",
                     "extended": "Extended day (three sessions Monday to Thursday)"}

# Tariff (cash case only). Extra income per robotic case over what the trust would
# earn for the same patient without the robot. All groups default to £0.
TARIFF_SOURCES = {
    "prostatectomy": ("To be entered. Robotic prostatectomy groups to a robotic-specific HRG in the NHS Payment Scheme. "
                      "Enter the 2026/27 unit price for that HRG (Annex A, August 2026 pay-award update) minus the "
                      "price the same patient's open operation would earn. The figure could not be extracted for v0.6."),
}
DEFAULT_TARIFF_SOURCE = "No robotic price difference identified: £0."
