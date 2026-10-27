# Changelog

## 0.5.1 (October 2026)

Fixes from local testing of v0.5.0.

- Unmet demand: a warning now fires for every specialty whose demand cannot be fully scheduled, including specialties that already have lists (for example, colorectal set to 20,000 leaves about 19,700 cases unscheduled). Each warning gives cases scheduled, cases not scheduled and the reason (robot fully booked, the 700-per-robot cap, or too little remaining demand to fill a list). Total unmet demand is shown on the Results tab and in the management case.
- Inputs tab: the internal group column (for example "colorectal", "abdominal_wall") is hidden.
- Tornado chart on the website: full assumption labels are shown, and chart height scales with the number of bars.
- Inputs tab: the 700 cap is explained. It limits the total robotic operations delivered per robot per year across all specialties, not any single input, and theatre sessions usually limit volume before the cap does.
- Wording corrections:
  - GIRFT (2025) says provision for surgical first assistants or care practitioners should be built into the business case. v0.5.0 described this as a requirement, which overstated it.
  - Sterilisation and proctoring are now described as items the guidance asks the business case to consider.
  - Donald et al (2026) use 500 to 750 procedures a year as a volume category. v0.5.0 implied that high-volume trusts performed that many.
  - The benchmark case mix is now stated as renormalised from the three specialties that made up 90% of UK NHS robotic procedures, with other specialties excluded.
- Tests: 477, up from 462. New tests cover the unmet-demand warnings and total, the hidden group column, full tornado labels and the corrected wording.

## 0.5.0 (October 2026)

Fixes from the review of v0.4, agreed before v2.

Corrections
- Break-even could report impossible volumes (for example 13,600 cases a year for two robots). It is now searched only up to the most the programme could deliver and is reported as reached, not reachable within capacity, or none. Shown on the website and in the Word case.
- The automatic list planner rounded demand to the nearest list. It left sessions empty while patients went unscheduled, and created lists it then flagged as unfillable. Lists are now created only if at least 75% full, with leftover demand pooled on a shared list. Medium DGH, one robot: 16 of 18 sessions booked, all demand scheduled, no under-filled lists.
- Robotic cases are capped at 700 per robot per year.
- Contract volumes apply per robot by default, configurable to per contract, and the basis is stated.

Changes to the headline
- The headline is the extra cost to the trust, by year and over five years, with no deduction for bed-days or any other 30-day cost avoided. Capital is shown separately. Cost per outcome uses the extra cost. Cost avoided and the discounted net present cost are in the economic case.
- Order is fixed in every output: patient consequences, cost per outcome, five-year cost.

New cost lines (placeholders unless stated)
- Surgical first assistant or care practitioner, 1 WTE per robot at £60,000. National guidance (NHS England and GIRFT, 2025) requires this in the business case; the cost is a placeholder.
- Sterile services, £75 per case.
- Theatre works, £50,000 per robot in year 1.

New features
- One-way sensitivity (tornado) on four results, replacing the single benefit multiplier.
- Benchmark programme shown side by side, with a source for every value.
- Assumptions register (Appendix D) with source, status and owner for each input.
- Cost-versus-cost-avoided chart.
- Save and reload inputs.
- Prostatectomy comparator: open by default; robotic surgery at another centre as a sensitivity scenario.
- Every page of the Word case carries a draft header.

Evidence and references
- Verified: J Robot Surg 2026;20:821 and World J Urol 2026 (single-port prostatectomy); PLoS One 2015 (Trastulli et al); NICE HTE21, now HealthTech guidance 742.
- Corrected: the title of the Surg Endosc 2024 colectomy conversion paper.
- Removed as unverified: two single-port details (18 v 35 hours; 18 minutes faster).
- Not re-verified, so flagged: Platform B's May 2026 capital anchor and Platform A's 15% uplift.
- Added: Donald et al 2026 (UK volumes and specialty mix); NHS England and GIRFT 2025; NBOCA 2025; the parliamentary answer on bed-day cost (elective inpatient £1,198 a day in 2024/25, including treatment costs, so not used as the value of a day saved).

Polish
- Internal labels replaced with readable text, money formatted throughout, and all package versions pinned (Streamlit 1.65.0).
- Tests: 462, up from 284.
