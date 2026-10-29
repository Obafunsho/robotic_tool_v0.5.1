# Worked example: Large hospital (>=800 beds), 1 robot, Platform D: single-port (purchase), exploratory, central evidence
Engine version 0.7.0. All inputs are placeholders for expert review.

## Step 1 to 3. Two-week theatre template
Template: standard. Each robot has 14 days x 3 sessions (AM session 1, PM session 2, PM session 3), one procedure per session. Standard hours are weekday sessions 1 and 2 (Friday session 2 maintenance); session 3 and weekend sessions count only when used. Cases per session follow complexity: High 1, Medium 1.5, Low 3, whole day 0.5.
Booked sessions per fortnight = 13; available = 18; utilisation = 13 / 18 = 72%.
Annual cases = cases per fortnight x 22.5 fortnights x 100% going ahead; then limited to demand (check on). Above 700 per robot a year is flagged amber (advisory), not cut.

| Procedure | Cases per fortnight | On template (year) | Demand | Delivered | Unmet |
| --- | --- | --- | --- | --- | --- |
| Radical prostatectomy (single-port) | 7.00 | 158 | 150 | 150 | 0 |
| Nephrectomy (partial, radical, nephroureterectomy) (single-port) | 3.00 | 68 | 60 | 60 | 0 |
| Lobectomy and transoral surgery (single-port) | 4.00 | 90 | 80 | 80 | 0 |

Cases per booked session by procedure: Radical prostatectomy 1; Nephrectomy 1.5; Lobectomy and transoral surgery 1.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Radical prostatectomy (single-port)):

- Robotic cases = 150.0 x 1.00 = 150.0
- Without the robot, 90% would have multi-port robot = 135.0 cases; bed-days saved = 1.00 x 135.0 x 0.5 = 67.5; conversions avoided = 0.00; complications avoided = 0.00; returns to theatre avoided = 0.00
- Without the robot, 10% would have open surgery = 15.0 cases; bed-days saved = 1.00 x 15.0 x 2 = 30.0; conversions avoided = 0.00; complications avoided = 0.30; returns to theatre avoided = 0.07
- Group totals: bed-days 97.5, complications 0.30, returns to theatre 0.07, readmissions 0.07

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 290.0 |
| Open operations avoided | 53.0 |
| Bed-days released | 232.1 |
| Conversions avoided | 0.5 |
| Reoperations avoided | 0.3 |
| Major complications avoided | 2.1 |
| Readmissions avoided | 0.4 |
| Extra elective cases enabled | 58.0 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £285,714
- Platform public dividend capital: £45,000
- Platform maintenance: £170,000
- Instruments = 290.0 x £2,500 = £725,000
- Sterile services = 290.0 x £75 = £21,750
- Surgical first assistant = 1 x 1 WTE x £60,000 = £60,000
- Extra theatre time = -95 min x £12 = £-1,140
- Extra cost to the trust = £1,306,324 (£4,505 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £104,645
- Extra cost less cost avoided = £1,201,680
- Extra tariff income (cash case only) = £0; net cash cost = £1,306,324

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 203 | 122 | £1,227,641 | £54,938 | £1,172,703 |
| 2 | 261 | 188 | £1,241,763 | £84,762 | £1,157,001 |
| 3 | 290 | 232 | £1,306,324 | £104,645 | £1,201,680 |
| 4 | 290 | 232 | £1,296,324 | £104,645 | £1,191,680 |
| 5 | 290 | 232 | £1,286,324 | £104,645 | £1,181,680 |
| Total | 1334 | 1006 | £6,358,377 | £453,634 | £5,904,743 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £5,352,963.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £4,766
- Extra cost per open operation avoided: £26,080
- Extra cost per bed-day released: £6,320
- Extra cost per serious event avoided: £523,691

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- Platform D: single-port (purchase), exploratory: the price is illustrative; enter the trust's quote.
- Booked utilisation 72% is below the 75% threshold: consider fewer robots or more specialties.
- 5 open sessions per fortnight left unbooked on the template.
