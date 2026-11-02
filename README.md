# Robotic programme decision engine (v1.1.0)

A transparent 30-day cost-consequence tool for NHS trusts deciding which robotic platform to procure, how many to buy, and how to fill them. No QALYs and no ICERs are computed, by design. The Word business case is the main output. Every output is marked as a draft until the assumptions register (a separate download from the tool) has been signed off. The tool uses a plain, NHS-familiar style but is not an NHS product and uses no NHS name or logo.

## Quick start

`pip install -r requirements.txt`, then `python -m pytest -q` (319 tests), then `streamlit run app.py`. To publish the tool, see DEPLOY.md.

The website is a single page. The main view holds only the essentials: hospital type (which sets the example rota), number of robots, platform, the rota, headline results and the Word business case. Everything else is in one "Advanced settings" section: existing robots, prostatectomy comparator, instrument price, central capital, contract basis, clinical benefit setting, rota operations that go ahead, the value of released bed-days, platform prices, unit costs, tariff uplift, procedure details, clinical assumptions, the assumptions register, detailed results, sensitivity and benchmark, and business case cover details. Each use is a one-off: inputs are not saved or reloaded. "Operations" is used for surgical activity throughout; "case" is kept for the business case.

Without the website: `python3 business_case.py examples/example_case.json out.docx`. Example outputs, two worked examples and the assumptions register are in `examples/`.

## Files

`app.py` web interface. `engine.py` calculations. `templates.py` the two-week robot rota. `defaults.py` every input, the procedure list, example rotas, the benchmark profile and readable labels. `evidence_review.py` the clinical lead's literature review applied as defaults (sources, evidence grades and statuses). `benchmark.py`, `sensitivity.py`, `register.py` benchmark, one-way (tornado) analysis and assumptions register. `register_xlsx.py` the Excel register (export and reload). `charts.py` charts for Word. `business_case.py` and `docx_render.py` the Word business case. `show_the_maths.py` a worked example. `.streamlit/config.toml` the theme; `static/` the favicon. `test_engine.py`, `test_app.py` the tests. `CHANGELOG.md` what changed.

## The main input: a two-week robot rota

The rota mirrors the clinical lead's rota sheet. Each robot has 14 days (Monday to Sunday, twice). For each day, choose the sessions available: 0, 2 or 3 (session 3 is unavailable on 2-session days; 0 is for days without robot sessions, such as weekends or maintenance days). For each session, choose a procedure and the number of operations (1 to 4), or "cont." for an operation continuing from the previous session with the same procedure; an operation may span 2 or 3 sessions. Simple cholecystectomy and simple inguinal hernia are not modelled. Utilisation = sessions booked / sessions available. Defaults: weekdays 2 sessions, weekends 0.

The hospital type only selects the starting example rota (robot 2 is pre-filled too for 2-robot proposals; users can clear it). No calculation depends on the hospital type. Complexity (High, Medium, Low) is descriptive only. There is no demand input.

## Procedures

The 17 procedures come from the clinical lead's list. From v0.8 their 30-day values follow the clinical lead's literature review of the register (`evidence_review.py`): changes that reduce benefit, add theatre time, or increase complication, conversion or reoperation benefit are applied, as are the radical cystectomy changes; changes that would increase length-of-stay benefit or the open share keep their v0.7 values. Complex cholecystectomy's 30-day effects are neutral (zero, clinical lead) with 12 extra minutes versus laparoscopic. Five procedures (complex breast, complex inguinal hernia, liver, oesophagogastric and pancreatoduodenectomy) have 30-day benefit not yet modelled, and every output flags this as "not yet modelled", not as no benefit. The gynaecology benefit applies to the whole population (about 90% of hysterectomies are benign); the business case notes the LACC trial's long-term finding, which is outside the 30-day scope.

## Assumptions register (Excel)

`register_xlsx.py` exports one row per procedure and assumption (254 rows) with ID, specialty, procedure, assumption, value, unit, source, evidence grade and status, then Decision (agree / change to / needs evidence), Change to and Comment. ID and Value are locked (sheet protection, no password). Reloading a completed file applies "change to" values as user-modified overrides and reads their Source and Evidence grade into the business case (Appendix C). The register is a separate download; the Word business case no longer reproduces it, but says where to find it. A "Change to" value without a decision, a value of the wrong type, an unknown decision, or a row the model no longer uses is reported as an error.

## Calculation chain

1. Rota: operations per fortnight by procedure, entered on the rota.
2. Annual operations = fortnight × 22.5 operating fortnights × share of rota operations that go ahead (the cancellation and under-run input, 100% by default). Above 700 operations per robot per year an amber advisory guardrail is shown; activity is not cut.
3. Counterfactual: of these operations, p_open would have been open without the robot, p_robot_elsewhere robotic elsewhere (prostatectomy sensitivity scenario), the rest laparoscopic.
4. Consequences: bed-days, conversions, returns to theatre, major complications and readmissions avoided, scaled by the evidence setting and learning curve.
5. Extra cost to the trust (the headline): platform + instruments + sterile services + surgical first assistant + extra theatre time + one-off implementation and theatre works. Nothing is deducted for 30-day cost avoided.
6. Tariff uplift (difference over existing tariff), cash case only: per robotic case, the difference over what the trust would earn for the same patient without the robot (radical prostatectomy £3,000 by default, others £0); net cash cost = extra cost − tariff uplift income. Tariff is a transfer within the NHS, so it is excluded from cost per outcome and the economic view.
7. Economic view: extra cost less 30-day cost avoided, discounted at 3.5%, capital in year 0, residual value credited at year 5.
8. Break-even: searched only up to every available session booked at the rota's procedure mix.

Outputs always show patient consequences first, then cost per outcome, then five-year cost.

## Tariff

The input is labelled "Tariff uplift (difference over existing tariff)" so that it is not mistaken for the full tariff. Radical prostatectomy defaults to £3,000 per operation (clinical lead, from the robotic urological surgery HRG, e.g. LB69Z: roughly £2,700 over the open and £3,400 over the laparoscopic tariff, averaged; the raw robotic tariff is about £8,000, but only the difference over existing tariffs counts). All other procedures default to £0. The value is editable and enters the trust's cash case only. Also unresolved: whether elective income is paid at full unit price or under aligned payment and incentive, and the market forces factor.

## Design and Streamlit limits

Plain, high-contrast layout familiar to NHS users: Arial, black text, simple tables, minimal toolbar (no Deploy button or menu), no emoji. The Word business case uses black text throughout, grey table headers and greyscale charts; only the yellow highlights on fields to complete and the red, amber and green guardrail cells keep colour. Limits that cannot be designed away:
- The editable rota is a canvas component: dropdown options are the same for every row, so invalid entries (for example "cont." after a different procedure, or an entry in an unavailable session 3) are flagged rather than prevented; long procedure names are truncated in the cell but shown in full in the dropdown. Very narrow screens scroll the rota sideways.
- Hiding chrome relies on Streamlit's internal identifiers; the version is pinned so this holds, but an upgrade may need the style block checking.
- On Streamlit Community Cloud the platform adds its own controls, which an app cannot remove. Self-hosting (DEPLOY.md) avoids them.

## Known limitations

Many clinical values, discounts and several unit costs remain placeholders or marked 'needs evidence'; the register lists each one. Complex abdominal wall repair uses 30-day assumptions set for ventral and incisional hernia (flagged); rectal resection, gynaecological oncology and lobectomy reuse carried-over values (flagged); six procedures have no modelled 30-day benefit yet. Evening and weekend sessions carry no staffing premium yet (v2 item 2). Long-term outcomes are not modelled.
