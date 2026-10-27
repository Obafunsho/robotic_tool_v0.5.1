# Worked example: Large hospital (>=800 beds), 1 robot, Platform D: single-port (purchase), exploratory, central evidence
Engine version 0.5.1. All inputs are placeholders for expert review.

## Step 1 to 3. Demand, capacity and plan
Capacity per fortnight = robots x sessions per week x 2 = 1 x 9 x 2 = 18.
Fortnights per year = 45 / 2 = 22.5.
A dedicated list is created only if it would be at least 75% full; leftover demand is pooled on shared half-day sessions, again only if they would be at least 75% full. Delivered cases are capped at 700 per robot per year.

| Group | Robotic cases available | Open without robot | Cases per list | List | Sessions/fortnight | Own lists | Shared list | Unmet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Single-port radical prostatectomy | 150 | 10% | 3 | all-day | 4 | 135 | 15 | 0 |
| Single-port kidney surgery (partial nephrectomy, pyeloplasty) | 60 | 30% | 3 | all-day | 2 | 60 | 0 | 0 |
| Single-port transoral surgery (head and neck) | 40 | 30% | 3 | all-day | 0 | 0 | 40 | 0 |
| Single-port transanal surgery (local excision of rectal lesions) | 50 | 20% | 2 | half-day | 1 | 45 | 5 | 0 |
| Single-port thoracic surgery (lung and mediastinal resection) | 40 | 20% | 2 | all-day | 2 | 40 | 0 | 0 |

Shared list: 2 half-day sessions per fortnight, 87% full.

Own-list cases = min(sessions x 22.5 x cases per list / sessions per list, cases available). Booked 11 of 18 sessions (61%). Robots needed to meet full demand: 0.57.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Single-port radical prostatectomy):

- Robotic cases = 150 x 1.00 = 150.0
- Without the robot, 90% would have multi-port robot = 135.0 cases; bed-days saved = 1.00 x 135.0 x 0.5 = 67.5; conversions avoided = 0.00; complications avoided = 0.00; returns to theatre avoided = 0.00
- Without the robot, 10% would have open surgery = 15.0 cases; bed-days saved = 1.00 x 15.0 x 2 = 30.0; conversions avoided = 0.00; complications avoided = 0.30; returns to theatre avoided = 0.07
- Group totals: bed-days 97.5, complications 0.30, returns to theatre 0.07, readmissions 0.07

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 340.0 |
| Open operations avoided | 63.0 |
| Bed-days released | 245.1 |
| Conversions avoided | 0.5 |
| Reoperations avoided | 0.4 |
| Major complications avoided | 2.7 |
| Readmissions avoided | 0.4 |
| Extra elective cases enabled | 61.3 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £285,714
- Platform public dividend capital: £45,000
- Platform maintenance: £170,000
- Instruments = 340.0 x £2,500 = £850,000
- Sterile services = 340.0 x £75 = £25,500
- Surgical first assistant = 1 x 1 WTE x £60,000 = £60,000
- Extra theatre time = 1005 min x £12 = £12,060
- Extra cost to the trust = £1,448,274 (£4,260 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £112,543
- Extra cost less cost avoided = £1,335,732

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 238 | 129 | £1,327,006 | £59,085 | £1,267,921 |
| 2 | 306 | 199 | £1,369,518 | £91,159 | £1,278,359 |
| 3 | 340 | 245 | £1,448,274 | £112,543 | £1,335,732 |
| 4 | 340 | 245 | £1,438,274 | £112,543 | £1,325,732 |
| 5 | 340 | 245 | £1,428,274 | £112,543 | £1,315,732 |
| Total | 1564 | 1063 | £7,011,347 | £487,872 | £6,523,476 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £5,908,845.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £4,483
- Extra cost per open operation avoided: £24,194
- Extra cost per bed-day released: £6,599
- Extra cost per serious event avoided: £468,806

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- Platform D: single-port (purchase), exploratory: the price is illustrative; enter the trust's quote.
- Booked utilisation 61% is below the 75% threshold: consider fewer robots or more specialties.
- 7 sessions per fortnight left unbooked: all demand entered is already scheduled.
