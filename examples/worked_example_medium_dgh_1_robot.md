# Worked example: Medium DGH (<800 beds), 1 robot, Platform B: established multi-port (purchase), central evidence
Engine version 0.5.1. All inputs are placeholders for expert review.

## Step 1 to 3. Demand, capacity and plan
Capacity per fortnight = robots x sessions per week x 2 = 1 x 9 x 2 = 18.
Fortnights per year = 45 / 2 = 22.5.
A dedicated list is created only if it would be at least 75% full; leftover demand is pooled on shared half-day sessions, again only if they would be at least 75% full. Delivered cases are capped at 700 per robot per year.

| Group | Robotic cases available | Open without robot | Cases per list | List | Sessions/fortnight | Own lists | Shared list | Unmet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Colorectal major resection (colon and rectum) | 120 | 10% | 2 | all-day | 4 | 90 | 30 | 0 |
| Nephrectomy and partial nephrectomy | 50 | 30% | 3 | all-day | 0 | 0 | 50 | 0 |
| Hysterectomy (benign and malignant) | 100 | 50% | 2 | half-day | 2 | 90 | 10 | 0 |
| Myomectomy | 25 | 80% | 1 | half-day | 1 | 22 | 2 | 0 |
| Endometriosis excision | 40 | 20% | 2 | all-day | 2 | 40 | 0 | 0 |
| Adnexal surgery | 30 | 10% | 3 | half-day | 0 | 0 | 30 | 0 |
| Abdominal wall (ventral and incisional hernia) | 80 | 70% | 2 | half-day | 2 | 80 | 0 | 0 |
| Upper GI (anti-reflux and hiatal hernia) | 20 | 5% | 2 | half-day | 0 | 0 | 20 | 0 |

Shared list: 5 half-day sessions per fortnight, 81% full.

Own-list cases = min(sessions x 22.5 x cases per list / sessions per list, cases available). Booked 16 of 18 sessions (89%). Robots needed to meet full demand: 0.81.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Colorectal major resection (colon and rectum)):

- Robotic cases = 120 x 1.00 = 120.0
- Without the robot, 10% would have open surgery = 12.0 cases; bed-days saved = 1.00 x 12.0 x 2 = 24.0; conversions avoided = 0.00; complications avoided = 0.48; returns to theatre avoided = 0.24
- Without the robot, 90% would have conventional minimal access (laparoscopic, endoscopic or laser) = 108.0 cases; bed-days saved = 1.00 x 108.0 x 0.5 = 54.0; conversions avoided = 5.40; complications avoided = 0.54; returns to theatre avoided = 0.54
- Group totals: bed-days 78.0, complications 1.02, returns to theatre 0.78, readmissions 0.12

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 465.0 |
| Open operations avoided | 165.0 |
| Bed-days released | 350.5 |
| Conversions avoided | 10.3 |
| Reoperations avoided | 1.4 |
| Major complications avoided | 6.3 |
| Readmissions avoided | 1.1 |
| Extra elective cases enabled | 87.6 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £274,286
- Platform public dividend capital: £43,200
- Platform maintenance: £150,000
- Instruments = 465.0 x £1,500 = £697,500
- Sterile services = 465.0 x £75 = £34,875
- Surgical first assistant = 1 x 1 WTE x £60,000 = £60,000
- Extra theatre time = 10930 min x £12 = £131,160
- Extra cost to the trust = £1,391,021 (£2,991 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £187,072
- Extra cost less cost avoided = £1,203,948

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 326 | 184 | £1,276,160 | £98,213 | £1,177,947 |
| 2 | 418 | 284 | £1,314,267 | £151,529 | £1,162,738 |
| 3 | 465 | 350 | £1,391,021 | £187,072 | £1,203,948 |
| 4 | 465 | 350 | £1,381,421 | £187,072 | £1,194,348 |
| 5 | 465 | 350 | £1,371,821 | £187,072 | £1,184,748 |
| Total | 2139 | 1519 | £6,734,690 | £810,959 | £5,923,730 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £5,369,438.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £3,149
- Extra cost per open operation avoided: £8,873
- Extra cost per bed-day released: £4,432
- Extra cost per serious event avoided: £175,346

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- 2 sessions per fortnight left unbooked: all demand entered is already scheduled.
