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

ENGINE_VERSION = "0.8.0"

# ---------------------------------------------------------------------------
# Procedures (clinical lead's list of 17; v0.8 values after the literature review)
# complexity        : High, Medium or Low. Descriptive only from v0.8: cases come from the rota
# benefit_status    : "modelled"; "not_yet_modelled" (zero placeholder pending evidence, never
#                     shown as "no benefit"); or "neutral" (zero by clinical lead decision)
# p_open            : of these robotic cases, the share that would be OPEN without the robot
#                     (the rest laparoscopic)
# p_robot_elsewhere : share that would have robotic surgery at another centre (prostatectomy
#                     sensitivity scenario)
# tariff_uplift     : extra income per robotic case over what the trust would earn anyway
#                     (cash case only)
# origin            : how the values were carried over, merged or split (v0.7) and reviewed (v0.8)
# Sources, evidence grades and statuses for every reviewed value: evidence_review.py
# ---------------------------------------------------------------------------
COMPLEXITY_LEVELS = ["High", "Medium", "Low"]
BENEFIT_STATUS_LABELS = {"modelled": "Modelled", "not_yet_modelled": "Not yet modelled",
                         "neutral": "Neutral (clinical lead)"}


def _g(label, specialty, complexity, p_open, nhse_priority, benefit_status, rationale, origin, **b):
    return dict(label=label, specialty=specialty, complexity=complexity, p_open=p_open,
                nhse_priority=nhse_priority, benefit_status=benefit_status,
                benefit_modelled=benefit_status != "not_yet_modelled",
                p_open_rationale=rationale, origin=origin, p_robot_elsewhere=0.0, tariff_uplift=0.0, **b)


PROCEDURE_GROUPS = {
    "bariatric_antireflux": _g(
        'Bariatric and anti-reflux surgery', 'Oesophagogastric', 'Medium', 0.05, False,
        'modelled',
        'Almost all laparoscopic without a robot.',
        'Carried over from upper GI (anti-reflux and hiatal hernia); bariatric surgery added.',
        los_reduction_open=2.0, los_reduction_lap=0.2, conv_reduction_lap=0.02, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.02, comp_reduction_lap=0.005, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),
    "colectomy": _g(
        'Colectomy (right, left, sigmoid)', 'Colorectal', 'Medium', 0.1, False,
        'modelled',
        'Most suitable cases are already laparoscopic; robot displaces some open (e.g. obese, pelvic, re-do).',
        'Carried over from colorectal major resection.',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.05, reop_reduction_open=0.02, reop_reduction_lap=0.005, comp_reduction_open=0.04, comp_reduction_lap=0.01, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=40.0),
    "abdo_wall_repair": _g(
        'Complex abdominal wall repair', 'Abdo wall complex', 'High', 0.7, True,
        'modelled',
        'Most ventral and incisional repairs are open without a robot.',
        'Carried over from abdominal wall reconstruction; 30-day assumptions still those set for ventral and incisional hernia (flagged).',
        los_reduction_open=1.5, los_reduction_lap=0.0, conv_reduction_lap=0.02, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.04, comp_reduction_lap=0.0, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=68.0, extra_minutes_lap=60.0),
    "benign_gyn": _g(
        'Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy)', "Women's health", 'Medium', 0.4667, True,
        'modelled',
        'Mix of hysterectomy, myomectomy and endometriosis counterfactuals, weighted by v0.7 case volumes.',
        'Merged: benign 70% of hysterectomy (70 cases), myomectomy (25) and endometriosis (40); assumptions weighted by v0.7 case volumes. Sacrocolpopexy added. Adnexal surgery dropped.',
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.01, reop_reduction_open=0.0041, reop_reduction_lap=0.0, comp_reduction_open=0.027, comp_reduction_lap=0.0, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=21.8519, extra_minutes_lap=40.0),
    "breast": _g(
        'Complex breast (mastectomy, flap reconstruction)', 'Breast', 'Medium', 1.0, False,
        'not_yet_modelled',
        'Placeholder: conventional (open) mastectomy is the usual alternative.',
        'New procedure. 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "cholecystectomy": _g(
        'Complex cholecystectomy', 'Hepatopancreatobiliary', 'Medium', 0.1, False,
        'neutral',
        'Placeholder: most complex cholecystectomies would otherwise be laparoscopic.',
        'New procedure. 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=12.0),
    "inguinal": _g(
        'Complex inguinal hernia', 'Abdo wall complex', 'Low', 0.3, False,
        'not_yet_modelled',
        'Placeholder: complex repairs would otherwise be open or laparoscopic.',
        'New procedure: complex repairs only (recurrent, bilateral or large); standard inguinal repair stays excluded as HVLC. 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=18.0),
    "paediatric": _g(
        'Complex paediatric (pyeloplasty, fundoplication, choledochal cyst)', 'Paediatric surgery', 'Medium', 0.5, True,
        'modelled',
        'Mixed open and laparoscopic without a robot.',
        'Carried over from paediatric; choledochal cyst added.',
        los_reduction_open=1.0, los_reduction_lap=0.2, conv_reduction_lap=0.02, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.01, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),
    "gyn_oncology": _g(
        'Gynaecological oncology (radical and cancer hysterectomy)', "Women's health", 'High', 0.5, True,
        'modelled',
        'Complex cases offered to the robot (large uterus, obesity) are often open otherwise.',
        'Split from hysterectomy (benign and malignant): malignant share 30% (placeholder); assumptions carried over from hysterectomy.',
        los_reduction_open=1.5, los_reduction_lap=0.2, conv_reduction_lap=0.04, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.04, comp_reduction_lap=0.0, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=30.0, extra_minutes_lap=20),
    "liver": _g(
        'Liver resection', 'Hepatopancreatobiliary', 'High', 0.7, False,
        'not_yet_modelled',
        'Placeholder: many liver resections are still open.',
        'New procedure (whole day). 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "lobectomy_transoral": _g(
        'Lobectomy and transoral surgery', 'Thoracic and head and neck', 'High', 0.8, False,
        'modelled',
        'Counterfactual is open access surgery; non-surgical treatment is not modelled.',
        'Carried over from head and neck (transoral robotic surgery); lobectomy added with the same placeholder assumptions (flagged).',
        los_reduction_open=3.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.01, reop_reduction_lap=0.0, comp_reduction_open=0.05, comp_reduction_lap=0.0, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=0),
    "nephrectomy": _g(
        'Nephrectomy (partial, radical, nephroureterectomy)', 'Urology', 'Medium', 0.3, False,
        'modelled',
        'Partial nephrectomy is often open without a robot; radical mostly laparoscopic.',
        'Carried over unchanged.',
        los_reduction_open=2.0, los_reduction_lap=0.3, conv_reduction_lap=0.03, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.03, comp_reduction_lap=0.005, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=20, extra_minutes_lap=15),
    "og_resection": _g(
        'Oesophagogastric resection', 'Oesophagogastric', 'High', 0.5, False,
        'not_yet_modelled',
        'Placeholder: many oesophagogastric resections are open or hybrid.',
        'New procedure (whole day). 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "whipple": _g(
        "Pancreatoduodenectomy (Whipple's)", 'Hepatopancreatobiliary', 'High', 0.95, False,
        'not_yet_modelled',
        'Placeholder: pancreatoduodenectomy is usually open.',
        'New procedure (whole day). 30-day benefit not yet modelled (zero placeholder).',
        los_reduction_open=0.0, los_reduction_lap=0.0, conv_reduction_lap=0.0, reop_reduction_open=0.0, reop_reduction_lap=0.0, comp_reduction_open=0.0, comp_reduction_lap=0.0, readm_reduction_open=0.0, readm_reduction_lap=0.0, extra_minutes_open=0.0, extra_minutes_lap=0.0),
    "cystectomy": _g(
        'Radical cystectomy', 'Urology', 'High', 0.8, False,
        'modelled',
        'Largely open without a robot.',
        'Carried over unchanged (whole day).',
        los_reduction_open=1.0, los_reduction_lap=0.5, conv_reduction_lap=0.03, reop_reduction_open=0.01, reop_reduction_lap=0.0, comp_reduction_open=0.03, comp_reduction_lap=0.01, readm_reduction_open=0.07, readm_reduction_lap=0.0, extra_minutes_open=60, extra_minutes_lap=20),
    "prostatectomy": _g(
        'Radical prostatectomy', 'Urology', 'High', 1.0, False,
        'modelled',
        'Comparator is open surgery. Robotic prostatectomy is established NHS practice, so robotic care at another centre is shown as a sensitivity scenario.',
        'Carried over unchanged. Cases per session fall from 1.5 to 1 under the complexity defaults.',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.02, reop_reduction_open=0.005, reop_reduction_lap=0.0, comp_reduction_open=0.02, comp_reduction_lap=0.005, readm_reduction_open=0.005, readm_reduction_lap=0.0, extra_minutes_open=0, extra_minutes_lap=0),
    "rectal": _g(
        'Rectal resection', 'Colorectal', 'High', 0.1, False,
        'modelled',
        'Most suitable cases are already laparoscopic; robot displaces some open (e.g. obese, pelvic, re-do).',
        'Carried over from colorectal major resection (same placeholder assumptions, flagged).',
        los_reduction_open=2.0, los_reduction_lap=0.5, conv_reduction_lap=0.05, reop_reduction_open=0.02, reop_reduction_lap=0.01, comp_reduction_open=0.04, comp_reduction_lap=0.01, readm_reduction_open=0.01, readm_reduction_lap=0.0, extra_minutes_open=30, extra_minutes_lap=20),
}
NOT_YET_MODELLED_TEXT = ("30-day benefit not yet modelled: zero is a placeholder pending evidence, "
                         "not a finding that the robot has no benefit")
NEUTRAL_TEXT = "30-day effects set to neutral (zero) by the clinical lead"

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
    "benign_gyn": ("Merged from hysterectomy, myomectomy and endometriosis (weighted by v0.7 case volumes). In England about half of "
                   "hysterectomies were laparoscopic by 2011-17 (Madhvani et al, cited in Clark and Saridogan 2021). "
                   "Effect sizes are placeholders."),
    "gyn_oncology": ("Carried over from hysterectomy (benign and malignant); conversion, complication and theatre-time "
                     "values updated from the literature review (endometrial cancer RCT review, J Robot Surg 2026). "
                     "The 30-day benefit is kept for the whole gynaecology population, as about 90% of hysterectomies "
                     "are benign. Outside the 30-day scope: the LACC trial (Ramirez et al, NEJM 2018) found worse "
                     "long-term survival after minimally invasive radical hysterectomy for early cervical cancer."),
    "abdo_wall_repair": ("Flagged for review: the 30-day assumptions were set for ventral and incisional hernia repair, "
                         "not complex abdominal wall repair. Open share placeholder; open repair remains the commonest "
                         "approach to hernia repair in UK national data (World J Emerg Surg 2025). Versus laparoscopy, "
                         "the PROVE-IT trial found no difference in complications or length of stay for ventral hernia."),
    "breast": ("Not yet modelled (zero). Evidence for review: in a randomised trial (80 women, Ann Surg 2022) "
               "complications did not differ between robotic and open nipple-sparing mastectomy; a meta-analysis "
               "(BJS 2024) found less nipple necrosis but a longer stay after robotic surgery."),
    "cholecystectomy": ("Neutral (clinical lead): all 30-day outcome effects set to zero; 12 extra theatre minutes "
                        "versus laparoscopic kept (literature review). US Medicare data associated robotic "
                        "cholecystectomy with more bile duct injury than laparoscopic (JAMA Surg 2023); a 2025 matched "
                        "cohort found longer stay and more major complications with the robot (JAMA Surg 2025)."),
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
    max_cases_per_robot=700,           # advisory: amber guardrail above this many cases per robot per year
    central_capital_per_robot=0,      # 0, 1,000,000 or 2,000,000: national capital injection (purchase only)
    include_capacity_value=False,     # True: value released bed-days as extra elective activity
    target_net_cost_per_bed_day=1500,  # placeholder target used for the instrument price calculation
    contribution_per_extra_case=1500, # placeholder: income less marginal cost per extra elective case
    realisation_factor=1.0,           # share of rota cases that go ahead (cancellations): placeholder 100%
)

# ---------------------------------------------------------------------------
# Presets: hospital type x number of robots
# ---------------------------------------------------------------------------
PRESETS = {
    # The hospital type only selects the starting example rota; no calculation depends on it.
    "medium_dgh_1": dict(label="Medium DGH (<800 beds), 1 robot", hospital="medium", robots=1),
    "medium_dgh_2": dict(label="Medium DGH (<800 beds), 2 robots", hospital="medium", robots=2),
    "large_1": dict(label="Large hospital (>=800 beds), 1 robot", hospital="large", robots=1),
    "large_2": dict(label="Large hospital (>=800 beds), 2 robots", hospital="large", robots=2),
}
EXISTING_ROBOT_OPTIONS = ["0", "1", "2", "3", "4", "5 or more"]


# ---------------------------------------------------------------------------
# Comparators (what patients would have without the robot)
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


NOT_MODELLED = set()


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
# Two-week robot rota (v0.8; mirrors the clinical lead's rota)
#
# Each robot has 14 days (Monday to Sunday, twice). Each day has "Sessions available"
# (0, 2 or 3; session 3 is unavailable on 2-session days). Each available session has a
# procedure dropdown and a cases dropdown: 1 to 4, or "cont." for a case continuing from
# the previous session with the same procedure (a case may span 2 or 3 sessions).
# Utilisation = sessions booked / sessions available. Maintenance is handled by setting
# fewer sessions available.
# ---------------------------------------------------------------------------
SESSIONS = ["AM", "PM", "Eve"]
SESSION_LABELS = {"AM": "Session 1 (AM)", "PM": "Session 2 (PM)", "Eve": "Session 3 (PM)"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS = DAYS[:5]
SESSIONS_AVAILABLE_OPTIONS = [0, 2, 3]
DEFAULT_SESSIONS = {d: (2 if d in WEEKDAYS else 0) for d in DAYS}
CASE_OPTIONS = ["1", "2", "3", "4", "cont."]
CONT = "cont."
MAX_SESSIONS_PER_CASE = 3
UNFILLED = "Unfilled session"

# Example rotas (starting points only; users edit or clear them). Each robot:
# {(week, day): [(procedure, cases), ...]} for sessions 1, 2, 3; unlisted weekdays have
# 2 sessions available and are unfilled; weekends 0.
_C = CONT
EXAMPLE_ROTAS = {
    "medium": [
        {(1, "Mon"): [("rectal", 1), ("rectal", _C)], (1, "Tue"): [("benign_gyn", 2), ("benign_gyn", 1)],
         (1, "Wed"): [("colectomy", 1), ("colectomy", 1)], (1, "Thu"): [("nephrectomy", 1), ("nephrectomy", 1)],
         (1, "Fri"): [("abdo_wall_repair", 1), ("inguinal", 3)],
         (2, "Mon"): [("colectomy", 1), ("colectomy", 1)], (2, "Tue"): [("benign_gyn", 2), ("gyn_oncology", 1)],
         (2, "Wed"): [("abdo_wall_repair", 1), ("abdo_wall_repair", 1)],
         (2, "Thu"): [("cholecystectomy", 2), ("bariatric_antireflux", 1)], (2, "Fri"): [("breast", 1)]},
        {(1, "Mon"): [("colectomy", 1), ("colectomy", 1)], (1, "Wed"): [("benign_gyn", 2), ("benign_gyn", 1)],
         (2, "Mon"): [("rectal", 1), ("rectal", _C)], (2, "Wed"): [("nephrectomy", 1), ("nephrectomy", 1)]},
    ],
    "large": [
        {(1, "Mon"): [("prostatectomy", 2), ("prostatectomy", 1)], (1, "Tue"): [("cystectomy", 1), ("cystectomy", _C)],
         (1, "Wed"): [("rectal", 1), ("rectal", 1)], (1, "Thu"): [("nephrectomy", 2), ("nephrectomy", 1)],
         (1, "Fri"): [("prostatectomy", 2), ("prostatectomy", 1)],
         (2, "Mon"): [("prostatectomy", 2), ("prostatectomy", 1)], (2, "Tue"): [("og_resection", 1), ("og_resection", _C)],
         (2, "Wed"): [("colectomy", 1), ("colectomy", 1)], (2, "Thu"): [("whipple", 1), ("whipple", _C)],
         (2, "Fri"): [("gyn_oncology", 1), ("gyn_oncology", 1)]},
        {(1, "Mon"): [("benign_gyn", 2), ("benign_gyn", 1)], (1, "Tue"): [("liver", 1), ("liver", _C)],
         (1, "Wed"): [("abdo_wall_repair", 1), ("abdo_wall_repair", 1)], (1, "Thu"): [("colectomy", 1), ("colectomy", 1)],
         (2, "Mon"): [("lobectomy_transoral", 1), ("lobectomy_transoral", 1)],
         (2, "Tue"): [("paediatric", 2), ("paediatric", 1)], (2, "Wed"): [("rectal", 1), ("rectal", 1)],
         (2, "Thu"): [("bariatric_antireflux", 2), ("cholecystectomy", 2)]},
    ],
}

# Tariff (cash case only). Extra income per robotic case over what the trust would
# earn for the same patient without the robot. All groups default to £0.
TARIFF_SOURCES = {
    "prostatectomy": ("A robotic tariff uplift exists: robotic prostatectomy groups to a robotic-specific HRG in the NHS "
                      "Payment Scheme. Left at £0 until the figure is supplied: enter the 2026/27 unit price for that "
                      "HRG minus the price the same patient's open operation would earn."),
}
DEFAULT_TARIFF_SOURCE = "No robotic price difference identified: £0."
