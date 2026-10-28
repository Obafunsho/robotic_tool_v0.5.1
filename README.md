# Robotic programme decision engine (v0.6.1)

A transparent 30-day cost-consequence tool for NHS trusts deciding which robotic platform to procure, how many to buy, and how to fill them. No QALYs and no ICERs are computed, by design. The Word business case is the main output. Every output is marked as a draft until the assumptions register (Appendix D of the business case) has been reviewed by the relevant specialties.

## Quick start

`pip install -r requirements.txt`, then `python -m pytest -q` (681 tests), then `streamlit run app.py`. The "Business case" tab downloads the Word document; inputs can be saved as a .json file and reloaded from the sidebar. To publish the tool, see DEPLOY.md.

Without the website: `python3 business_case.py examples/example_case.json out.docx`. Example outputs and three worked examples are in `examples/`.

## Files

`app.py` web interface. `engine.py` calculations. `templates.py` the two-week theatre template. `defaults.py` every placeholder input, list types, the benchmark profile and readable labels. `benchmark.py`, `sensitivity.py`, `register.py` benchmark, one-way (tornado) analysis and assumptions register. `charts.py` charts for Word. `inputs_io.py` saving and reloading cases. `business_case.py` and `docx_render.py` the Word business case. `show_the_maths.py` a worked example. `.streamlit/config.toml` the theme (Streamlit's bundled Source Sans and Source Serif); `static/` the favicon. `test_engine.py`, `test_app.py` the tests. `CHANGELOG.md` what changed.

## The main input: a two-week theatre template

Each robot has 14 days (Monday to Sunday, twice) with AM, PM and evening sessions. For each session the user picks a list type and the cases on it: a combination of major, medium and minor cases up to the session maximum (3 by default, adjustable), "Continuing" for a case running on from the previous session, or "Closed". Templates are pre-filled for each hospital preset (weekday AM and PM, Friday PM for maintenance; evenings and weekends blank) and in an extended-day variant (three sessions Monday to Thursday). Pre-filling, and "Suggest a template from this demand", fill sessions until demand is met or sessions run out: each session goes to the list type that adds the most unmet demand, trimmed to the cases still needed, and the extended day uses evenings only for demand that weekday daytime sessions cannot absorb.

Standard hours are weekday AM and PM: a blank standard session is open but unbooked. Evening and weekend sessions count only when booked ("Empty" offers one without booking it). Utilisation = booked sessions / available sessions.

Each list type's tiers map to procedure groups (Appendix A of the business case). Prostate, kidney and bladder lists use the medium tier. Gynaecology major cases split 40% hysterectomy, 50% endometriosis, 10% myomectomy (clinical lead's estimate of the mix within a gynaecology major session, being confirmed); gynaecology minor cases are adnexal surgery. Demand is entered separately and keeps the v0.5 placeholders; where the split differs from the demand mix, a warning explains that meeting demand for one procedure over-schedules another. A tier mapped to nothing counts as "not modelled": costed, with no 30-day benefit. The mapping and splits are editable in an advanced table and any change is flagged as user-modified.

Annual demand is optional, in "Check against demand". When the check is on, delivered cases cannot exceed demand, unmet demand is reported for every procedure, and lists that demand cannot fill at least 75% are flagged. "Suggest a template from this demand" rebuilds the grid from demand. The v0.5 demand-led list planner remains in the engine (`template=None`) and underpins the suggestion and the benchmark.

## Calculation chain

1. Template: cases per fortnight by procedure group, from each booked session's tiers and the mapping.
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
- The editable grid is a canvas component: it shows an empty dropdown cell as "None", so blanks are held as a non-breaking space on screen and converted back; dropdown options are the same for every row, so one dropdown cannot depend on another (incompatible list type and case entries are flagged rather than prevented), and cells cannot be coloured while editing. The read-only template on the Results tab is colour-coded.
- Hiding chrome relies on Streamlit's internal identifiers; the version is pinned so this holds, but an upgrade may need the style block checking.
- On Streamlit Community Cloud the platform adds its own controls and badge, which an app cannot remove. Self-hosting (DEPLOY.md) avoids them.
- Every edit reruns the page; the "running" indicator stays visible. Layout is limited to columns, tabs and expanders, and narrow mobile screens are not well served.

## Known limitations

Clinical priors, demand, discounts, several unit costs and the tariff are placeholders awaiting review; the register lists each one. Abdominal wall reconstruction uses 30-day assumptions set for ventral and incisional hernia (flagged). Evening and weekend sessions carry no staffing premium yet (v2 item 2). Long-term outcomes are not modelled.
