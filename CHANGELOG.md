# Changelog

## 0.6.1 (October 2026)

Fixes from browser and template testing of v0.6.0.

- Default templates and "Suggest a template from this demand" now fill sessions until demand is met or sessions run out. v0.6.0 stopped early: the medium DGH default left 4 sessions a fortnight unbooked while 85 cases a year went unscheduled, which repeated the v0.4 planner issue.
  - Each session goes to the list type that adds the most demand still unmet, using its session pattern trimmed to the cases still needed.
  - A list keeps the rest of its day while it still adds cases, and a 'Continuing' case is always completed.
  - The extended day uses Monday to Thursday evenings only for demand that weekday daytime sessions cannot absorb.
  - The fill allows for the cancellation factor.
  - Checked for every preset, both platforms and both variants: no open session is left while demand goes unmet.
- Fonts: in Chromium the whole site rendered in Times New Roman, because the theme's custom font faces never registered. The theme now uses Streamlit's bundled faces ("sans-serif" is Source Sans, "serif" is Source Serif). Confirmed in headless Chromium: both faces load and are applied to the body and headings. The font files and their licence texts were removed from static/.
- Empty grid cells showed "None". They now display blank: a non-breaking space on screen, converted back to an empty entry.
- The 700 cases per robot per year is now an amber advisory guardrail ("Robotic cases per robot per year"), not a cut. Break-even is searched up to every available session filled.
- New input: templated cases that go ahead (%), for cancellations and under-runs, default 100%. It is saved and reloaded with the case.
- Gynaecology demand reverted to the v0.5 placeholders: hysterectomy 100/160, endometriosis 40/60, myomectomy 25/40 (medium/large); the benchmark's gynaecology split is reverted too. The 40/50/10 split describes cases within a gynaecology major session, not the trust's demand, so v0.6.0 should not have changed the demand inputs. Where the split and the demand mix disagree, a new warning explains that meeting demand for one procedure over-schedules another.
- Default results change. Medium DGH, 1 robot, standard day: 18 of 18 sessions booked, 410 cases a year delivered, 55 unmet (abdominal wall reconstruction 35, upper GI 20). The extended day meets all demand (465 cases).
- Tests: 681, up from 635. New tests cover filling until demand is met, blank cells, the advisory 700 level and the cancellation input.

## 0.6.0 (October 2026)

The main input is now a two-week theatre template, following the clinical lead's review.

Template
- Each robot has 14 days (Monday to Sunday, twice) × AM, PM and evening sessions. Each session takes a list type and a case entry: combinations of major, medium and minor cases up to a session maximum (3 by default, adjustable), "Continuing", "Empty", "Closed" or "Maintenance".
- The fortnight is extrapolated to a year (22.5 operating fortnights). Utilisation = booked sessions ÷ available sessions. Standard hours are weekday AM and PM; evenings and weekends count only when used.
- Pre-filled templates for every preset: weekday AM and PM, Friday PM for maintenance. An optional extended-day variant uses three sessions Monday to Thursday. Templates are built from demand by a new suggest-from-demand routine, also available as a button.
- Entries are validated, and problems become warnings: 'Continuing' without a booked session before it, cases without a list type, a list type without cases, and more cases than the session maximum.

List types and tiers
- A medium tier is added. Prostate, kidney and bladder lists are medium.
- Abdominal wall major cases are renamed abdominal wall reconstruction. Their 30-day assumptions, set for ventral and incisional hernia, are flagged for review in the register.
- The gynaecology major split is 40% hysterectomy, 50% endometriosis, 10% myomectomy, pending confirmation. The gynaecology demand placeholders were re-split to match, keeping each preset's total; the benchmark's gynaecology split was aligned too.
- The tier mapping and splits are editable in an advanced table and flagged as user-modified when changed. Unmapped tiers count as "not modelled": costed, no 30-day benefit.

Demand, warnings and the cap
- Annual demand becomes an optional check. When on, delivered cases are limited to demand, unmet demand is reported for every procedure, and template lists that demand cannot fill at least 75% are flagged.
- The 700-cases-per-robot cap stays hard. The large-hospital extended-day template reaches it.
- The v0.5 planner is kept for the suggestion routine, the benchmark and legacy cases.

Tariff (cash case only)
- New input: extra income per robotic case over what the trust would earn anyway, per procedure. It reduces the trust's net cash cost and is excluded from cost per outcome and the economic view. The business case states the assumption.
- All values default to £0. Robotic prostatectomy is a flagged placeholder because its 2026/27 NHS Payment Scheme price could not be extracted. Other unknowns are listed in the register: the payment mechanism (aligned payment and incentive), the market forces factor, and the assumption that patients would otherwise be treated at the same trust.

Design
- Restrained institutional theme: Source Sans 3 and Source Serif 4 (served locally, SIL Open Font Licence), navy accent, minimal toolbar (no Deploy button or menu), a plain favicon and no emoji. The Streamlit limits are documented in the README.

Other
- Tornado: a new parameter, "share of templated cases that go ahead", and a net cash metric.
- Word: the management case shows the template for each robot and a procedure table. Appendix A shows the tier mapping and tariff.
- Results: the colour-coded read-only template; a per-procedure table of templated, delivered and unmet cases.
- Default results change because the inputs changed. For example, the medium DGH default now delivers about 380 cases a year, down from 465, mainly because abdominal wall reconstruction takes one case per session.
- Tests: 635, up from 477. New tests cover the grid, medium tier, editable splits and tariff.

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
