# Robotic programme decision engine (v0.7.0)

A transparent 30-day cost-consequence tool for NHS trusts deciding which robotic platform to procure, how many to buy, and how to fill them. No QALYs and no ICERs are computed, by design. The Word business case is the main output. Every output is marked as a draft until the assumptions register (Appendix D of the business case) has been reviewed by the relevant specialties.

## Quick start

`pip install -r requirements.txt`, then `python -m pytest -q` (647 tests), then `streamlit run app.py`. The "Business case" tab downloads the Word document; inputs can be saved as a .json file and reloaded from the sidebar. To publish the tool, see DEPLOY.md.

Without the website: `python3 business_case.py examples/example_case.json out.docx`. Example outputs and three worked examples are in `examples/`.

## Files

`app.py` web interface. `engine.py` calculations. `templates.py` the two-week theatre template. `register_xlsx.py` the Excel assumptions register (export and reload). `defaults.py` every placeholder input, list types, the benchmark profile and readable labels. `benchmark.py`, `sensitivity.py`, `register.py` benchmark, one-way (tornado) analysis and assumptions register. `charts.py` charts for Word. `inputs_io.py` saving and reloading cases. `business_case.py` and `docx_render.py` the Word business case. `show_the_maths.py` a worked example. `.streamlit/config.toml` the theme (Streamlit's bundled Source Sans and Source Serif); `static/` the favicon. `test_engine.py`, `test_app.py` the tests. `CHANGELOG.md` what changed.

## The main input: a two-week theatre template

Each robot has 14 days (Monday to Sunday, twice) with three sessions: "AM session 1", "PM session 2" and "PM session 3". Each session has one dropdown: "Unfilled session", one of 17 procedures shown as "Specialty – Procedure", "Maintenance" or "Closed". Weekday sessions 1 and 2 are standard hours: an unfilled one is open but unbooked. Session 3 and weekend sessions count only when booked. Friday session 2 is kept for maintenance by default. Utilisation = booked sessions / available sessions.

Case counts are hidden from the user. Each booked session counts as the procedure's cases per session, set by its complexity: High 1, Medium 1.5, Low 3. Whole-day procedures (radical cystectomy, pancreatoduodenectomy, oesophagogastric resection, liver resection) count 0.5 per session, so one case across sessions 1 and 2, and are flagged if booked for only one session of a day. Complexity, cases per session and whole day are editable in the advanced procedure table, and changes are flagged.

Templates are pre-filled for each preset (standard day, or extended day with session 3 Monday to Thursday) by filling sessions until demand is met or sessions run out; "Suggest a template from this demand" uses the same routine. Annual demand is optional ("Check against demand").

## Procedures (v0.7)

The 17 procedures come from the clinical lead's list, each with specialty and complexity. Carried-over assumptions: colectomy and rectal resection from colorectal major resection (demand split 60:40); complex benign gynaecology merged from benign hysterectomy, myomectomy and endometriosis (averaged by demand; adnexal surgery dropped); gynaecological oncology from the malignant 30% of hysterectomy; complex abdominal wall repair, bariatric and anti-reflux surgery, complex paediatric, and lobectomy and transoral surgery from their v0.6 equivalents; nephrectomy, radical cystectomy and radical prostatectomy unchanged. Six new procedures (complex breast, complex cholecystectomy, complex inguinal hernia, liver resection, oesophagogastric resection, pancreatoduodenectomy) have a zero 30-day benefit until evidence is reviewed; every output flags this as "not yet modelled", not as no benefit. Only complex inguinal repairs are included; standard inguinal repair remains excluded as high-volume low-complexity work.

The single-port platform is restricted to radical prostatectomy, nephrectomy, and lobectomy and transoral surgery (single-port transoral and thoracic groups merged). Single-port transanal surgery was dropped, so a medium DGH has no eligible single-port demand.

## Assumptions register (Excel)

`register_xlsx.py` exports one row per procedure and assumption (multi-port and single-port, about 400 rows) with ID, specialty, procedure, assumption, value, unit, source, evidence grade and status, then Decision (agree / change to / needs evidence), Change to and Comment. ID and Value are locked (sheet protection, no password). Reloading a completed file (website, or `register_xlsx.load`) applies "change to" values as user-modified overrides; demand changes apply to the matching hospital size. "Needs evidence" items and comments are listed in Appendix D of the business case.

## Calculation chain

1. Template: cases per fortnight by procedure, from each booked session's cases per session.
2. Annual cases = fortnight × 22.5 operating fortnights × share of templated cases that go ahead (the cancellation and under-run input, 100% by default); limited to demand if the check is on. Above 700 cases per robot per year an amber advisory guardrail is shown; activity is not cut.
3. Counterfactual: of these cases, p_open would have been open without the robot, p_robot_elsewhere robotic elsewhere (prostatectomy sensitivity scenario), the rest laparoscopic.
4. Consequences: bed-days, conversions, returns to theatre, major complications and readmissions avoided, scaled by the evidence setting and learning curve.
5. Extra cost to the trust (the headline): platform + instruments + sterile services + surgical first assistant + extra theatre time + one-off implementation and theatre works. Nothing is deducted for 30-day cost avoided.
6. Tariff (cash case only): extra income per robotic case over what the trust would earn for the same patient without the robot, per procedure; net cash cost = extra cost − tariff income. Tariff is a transfer within the NHS, so it is excluded from cost per outcome and the economic view.
7. Economic view: extra cost less 30-day cost avoided, discounted at 3.5%, capital in year 0, residual value credited at year 5.
8. Break-even: searched only up to every available session filled at the template's case mix.

Outputs always show patient consequences first, then cost per outcome, then five-year cost.

## Tariff

All procedures default to £0. Robotic prostatectomy groups to a robotic-specific HRG, but the 2026/27 NHS Payment Scheme price (Annex A workbook, August 2026 pay-award update) could not be extracted for this build, so it is a flagged placeholder: enter the robotic HRG price minus the open-operation price. Also unresolved: whether elective income is paid at full unit price or under aligned payment and incentive, and the market forces factor.

## Streamlit limits

The theme, fonts, colours and minimal toolbar are set in `.streamlit/config.toml`; a short style block hides the remaining default chrome. Fonts use Streamlit's bundled faces ("sans-serif" is Source Sans, "serif" is Source Serif): custom `[[theme.fontFaces]]` did not register in Chromium in v0.6.0, and the whole site fell back to Times New Roman. Limits that cannot be designed away:
- The editable grid is a canvas component: long option labels are truncated in the cell (the full label shows in the dropdown); dropdown options are the same for every row, so one dropdown cannot depend on another (a whole-day procedure booked for one session is flagged rather than prevented), and cells cannot be coloured while editing. The read-only template on the Results tab is colour-coded.
- Hiding chrome relies on Streamlit's internal identifiers; the version is pinned so this holds, but an upgrade may need the style block checking.
- On Streamlit Community Cloud the platform adds its own controls and badge, which an app cannot remove. Self-hosting (DEPLOY.md) avoids them.
- Every edit reruns the page; the "running" indicator stays visible. Layout is limited to columns, tabs and expanders, and narrow mobile screens are not well served.

## Known limitations

Clinical priors, demand, discounts, several unit costs and the tariff are placeholders awaiting review; the register lists each one. Complex abdominal wall repair uses 30-day assumptions set for ventral and incisional hernia (flagged); rectal resection, gynaecological oncology and lobectomy reuse carried-over values (flagged); six procedures have no modelled 30-day benefit yet. Evening and weekend sessions carry no staffing premium yet (v2 item 2). Long-term outcomes are not modelled.
