# Worked example: Medium DGH (<800 beds), 1 robot (example rota), Platform B: established multi-port (purchase), central evidence
Engine version 0.8.0. All inputs are placeholders for expert review. The hospital type only selects the example rota.

## Step 1 to 2. Two-week robot rota
Each robot has 14 days. For each day the trust sets the sessions available (0, 2 or 3); for each session, a procedure and its cases (1 to 4, or 'cont.' for a case continuing from the previous session).
Sessions booked per fortnight = 19; available = 20; utilisation = 19 / 20 = 95%.
Annual cases = cases per fortnight x 22.5 fortnights x 100% going ahead. Above 700 per robot a year is flagged amber (advisory), not cut.

| Procedure | Sessions per fortnight | Cases per fortnight | Cases a year |
| --- | --- | --- | --- |
| Bariatric and anti-reflux surgery | 1 | 1 | 22.5 |
| Colectomy (right, left, sigmoid) | 4 | 4 | 90.0 |
| Complex abdominal wall repair | 3 | 3 | 67.5 |
| Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy) | 3 | 5 | 112.5 |
| Complex breast (mastectomy, flap reconstruction) | 1 | 1 | 22.5 |
| Complex cholecystectomy | 1 | 2 | 45.0 |
| Complex inguinal hernia | 1 | 3 | 67.5 |
| Gynaecological oncology (radical and cancer hysterectomy) | 1 | 1 | 22.5 |
| Nephrectomy (partial, radical, nephroureterectomy) | 2 | 2 | 45.0 |
| Rectal resection | 2 | 1 | 22.5 |

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy)):

- Robotic cases = 112.5 x 1.00 = 112.5
- Without the robot, 47% would have open surgery = 52.5 cases; bed-days saved = 1.00 x 52.5 x 1.5 = 78.8; conversions avoided = 0.00; complications avoided = 1.42; returns to theatre avoided = 0.22
- Without the robot, 53% would have conventional minimal access (laparoscopic, endoscopic or laser) = 60.0 cases; bed-days saved = 1.00 x 60.0 x 0.2 = 12.0; conversions avoided = 0.60; complications avoided = 0.00; returns to theatre avoided = 0.00
- Group totals: bed-days 90.8, complications 1.42, returns to theatre 0.22, readmissions 0.26

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 517.5 |
| Open operations avoided | 184.1 |
| Bed-days released | 296.9 |
| Conversions avoided | 7.9 |
| Reoperations avoided | 1.4 |
| Major complications avoided | 5.9 |
| Readmissions avoided | 1.0 |
| Extra elective cases enabled | 74.2 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £274,286
- Platform public dividend capital: £43,200
- Platform maintenance: £150,000
- Instruments = 517.5 x £1,500 = £776,250
- Sterile services = 517.5 x £75 = £38,812
- Surgical first assistant = 1 x 1 WTE x £60,000 = £60,000
- Extra theatre time = 15060 min x £12 = £180,725
- Extra cost to the trust = £1,523,273 (£2,944 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £161,188
- Extra cost less cost avoided = £1,362,085
- Extra tariff income (cash case only) = £0; net cash cost = £1,523,273

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 362 | 156 | £1,368,737 | £84,624 | £1,284,113 |
| 2 | 466 | 240 | £1,433,294 | £130,563 | £1,302,732 |
| 3 | 518 | 297 | £1,523,273 | £161,188 | £1,362,085 |
| 4 | 518 | 297 | £1,513,673 | £161,188 | £1,352,485 |
| 5 | 518 | 297 | £1,504,073 | £161,188 | £1,342,885 |
| Total | 2380 | 1287 | £7,343,051 | £698,751 | £6,644,299 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £6,016,283.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £3,085
- Extra cost per open operation avoided: £8,670
- Extra cost per bed-day released: £5,706
- Extra cost per serious event avoided: £204,167

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- 30-day benefit not yet modelled for Complex breast (mastectomy, flap reconstruction) (22 cases a year), Complex inguinal hernia (68 cases a year): their benefit is a zero placeholder pending evidence, not a finding that the robot has no benefit.
- 1 available session per fortnight left unfilled on the rota.
