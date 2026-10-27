# Robotic programme decision engine (v0.5.1)

A transparent 30-day cost-consequence engine for NHS trusts deciding which robotic platform to procure, how many to buy, and how to fill them. No QALYs and no ICERs are computed, by design. Every output is marked as a draft until the assumptions register (Appendix D of the business case) has been reviewed by the relevant specialties.

## Quick start

`pip install -r requirements.txt`, then `python -m pytest -q` (477 tests), then `streamlit run app.py`. The "Business case" tab downloads the Word document; inputs can be saved as a .json file and reloaded from the sidebar. To publish the tool, see DEPLOY.md.

Without the website: `python3 business_case.py examples/example_case.json out.docx`. Example outputs and three worked examples are in `examples/`.

## Files

`app.py` web interface. `engine.py` calculations. `defaults.py` every placeholder input, the benchmark profile and readable labels. `benchmark.py` the benchmark programme. `sensitivity.py` one-way (tornado) analysis. `register.py` assumptions register. `charts.py` charts for Word. `inputs_io.py` saving and reloading cases. `business_case.py` and `docx_render.py` the Word business case. `show_the_maths.py` prints a worked example. `test_engine.py` and `test_app.py` the test suite. `CHANGELOG.md` what changed.

## Calculation chain

For procedure group g in year t:

1. Demand: annual robotic cases available for group g, entered in one step.
2. Capacity: sessions per fortnight = robots × sessions per robot per week × 2.
3. Plan: whole lists (half-day = 1 session, all-day = 2). A dedicated list is created only if it would be at least 75% full, priority specialties first; further lists go to the least-filled group (or, optionally, the group with most 30-day cost avoided per session), again only if at least 75% full. Remaining capacity is offered as shared half-day sessions that pool every group's leftover demand, only if the shared sessions would be at least 75% full. Spare sessions are left empty and reported with the reason.
4. Cases: own-list cases = min(sessions × fortnights × cases per session, demand); shared cases are divided in proportion to each group's leftover demand. The total across all specialties is capped at 700 robotic operations per robot per year (individual demand inputs are not capped; theatre sessions usually limit volume first), then multiplied by utilisation in year t. Every specialty with demand that cannot be scheduled gets a warning, and total unmet demand is reported.
5. Counterfactual: of these cases, p_open would have been open without the robot, p_robot_elsewhere would have had robotic surgery at another centre (no 30-day difference; used for the prostatectomy sensitivity scenario) and the rest laparoscopic. Prostatectomy keeps open surgery as its default comparator.
6. Consequences, with multiplier m_t = evidence setting × learning factor_t: bed-days, conversions, returns to theatre, major complications and readmissions avoided.
7. Extra cost to the trust (the headline): platform (by payment model) + instruments + sterile services + surgical first assistant + extra theatre time + one-off implementation and theatre works. Nothing is deducted for 30-day cost avoided. Capital is reported separately.
8. Cost avoided: events avoided × unit costs. Economic view only; it is not cash.
9. Economic view: extra cost less cost avoided, discounted at 3.5% with capital in year 0 and residual value credited at year 5.
10. Break-even: the steady-state volume at which cost avoided covers the extra cost, searched only up to the most the programme could deliver (the lower of the 700-per-robot cap and every session filled at the planned case mix). Reported as reached, not reachable within capacity, or none.

Cost per outcome = five-year extra cost ÷ each consequence. Ratios are descriptive and must not be added. Outputs always show patient consequences first, then cost per outcome, then five-year cost.

## Rules that protect credibility

Length-of-stay reduction is the total difference in index stay, including stay caused by complications; event unit costs are therefore non-ward costs only, except readmission. Extra theatre time is costed and not scaled by the evidence setting. Any assumption changed from the default is listed, with a readable label, in every output. Supplier names are never used.

## Sensitivity analysis

`sensitivity.py` moves each assumption on its own to a low and a high value (capital, maintenance, instrument price, sterile services, first assistant, theatre minutes and cost per minute, utilisation, share open, bed-days saved, other events avoided, learning curve, bed-day cost, and the prostatectomy comparator) with the list plan held fixed. Results: five-year extra cost, extra cost per bed-day released, extra cost per open operation avoided, or net present cost. Ranges are placeholders. The scenario table (no benefit, halved, 1.5 times, instrument prices, central capital, prostatectomy at another centre) is kept alongside.

## Benchmark

A well-functioning multi-port programme (550 cases per robot a year, a project-team assumption; case mix renormalised from the three specialties, urology, general surgery and gynaecology, that made up 90% of UK NHS robotic procedures in 2024 (Donald et al, Surg Endosc 2026), other specialties excluded; mid-level costs) is run through the same engine with the trust's clinical assumptions, unit costs and capital source, and shown side by side. Every benchmark value carries its source or is labelled an assumption.

## Perspective switches

Central capital of £0, £1M or £2M per robot (purchase models). Instrument price: list, 15% off, 30% off, or a trust quote. Contract volumes (cases included under a managed service, minimum cases under a per-procedure fee) apply per robot by default or per contract; the basis is stated in the output. Capacity value: optionally values released bed-days as extra elective activity (economic view only).

## Known limitations

Clinical priors, volumes, discounts and several unit costs are placeholders awaiting specialty and finance review; the register lists each one. Platform B's capital anchor and Platform A's uplift were not re-verified in v0.5. Long-term functional, oncological and hernia outcomes are not modelled. Staffing for genuinely new theatre lists, surgeon capacity limits, the national allocation view, the 12-month review screen, and VAT and impairment are planned for v2.
