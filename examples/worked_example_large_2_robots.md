# Worked example: Large hospital (>=800 beds), 2 robots (example rota), Platform B: established multi-port (purchase), central evidence
Engine version 0.8.0. All inputs are placeholders for expert review. The hospital type only selects the example rota.

## Step 1 to 2. Two-week robot rota
Each robot has 14 days. For each day the trust sets the sessions available (0, 2 or 3); for each session, a procedure and its cases (1 to 4, or 'cont.' for a case continuing from the previous session).
Sessions booked per fortnight = 36; available = 40; utilisation = 36 / 40 = 90%.
Annual cases = cases per fortnight x 22.5 fortnights x 100% going ahead. Above 700 per robot a year is flagged amber (advisory), not cut.

| Procedure | Sessions per fortnight | Cases per fortnight | Cases a year |
| --- | --- | --- | --- |
| Bariatric and anti-reflux surgery | 1 | 2 | 45.0 |
| Colectomy (right, left, sigmoid) | 4 | 4 | 90.0 |
| Complex abdominal wall repair | 2 | 2 | 45.0 |
| Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy) | 2 | 3 | 67.5 |
| Complex cholecystectomy | 1 | 2 | 45.0 |
| Complex paediatric (pyeloplasty, fundoplication, choledochal cyst) | 2 | 3 | 67.5 |
| Gynaecological oncology (radical and cancer hysterectomy) | 2 | 2 | 45.0 |
| Liver resection | 2 | 1 | 22.5 |
| Lobectomy and transoral surgery | 2 | 2 | 45.0 |
| Nephrectomy (partial, radical, nephroureterectomy) | 2 | 3 | 67.5 |
| Oesophagogastric resection | 2 | 1 | 22.5 |
| Pancreatoduodenectomy (Whipple's) | 2 | 1 | 22.5 |
| Radical cystectomy | 2 | 1 | 22.5 |
| Radical prostatectomy | 6 | 9 | 202.5 |
| Rectal resection | 4 | 4 | 90.0 |

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Radical prostatectomy):

- Robotic cases = 202.5 x 1.00 = 202.5
- Without the robot, 100% would have open surgery = 202.5 cases; bed-days saved = 1.00 x 202.5 x 2 = 405.0; conversions avoided = 0.00; complications avoided = 4.05; returns to theatre avoided = 1.01
- Without the robot, 0% would have conventional minimal access (laparoscopic, endoscopic or laser) = 0.0 cases; bed-days saved = 1.00 x 0.0 x 0.5 = 0.0; conversions avoided = 0.00; complications avoided = 0.00; returns to theatre avoided = 0.00
- Group totals: bed-days 405.0, complications 4.05, returns to theatre 1.01, readmissions 1.01

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 900.0 |
| Open operations avoided | 469.1 |
| Bed-days released | 898.4 |
| Conversions avoided | 12.7 |
| Reoperations avoided | 3.6 |
| Major complications avoided | 13.2 |
| Readmissions avoided | 3.5 |
| Extra elective cases enabled | 224.6 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £548,571
- Platform public dividend capital: £86,400
- Platform maintenance: £300,000
- Instruments = 900.0 x £1,500 = £1,350,000
- Sterile services = 900.0 x £75 = £67,500
- Surgical first assistant = 2 x 1 WTE x £60,000 = £120,000
- Extra theatre time = 18065 min x £12 = £216,781
- Extra cost to the trust = £2,689,252 (£2,988 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £455,568
- Extra cost less cost avoided = £2,233,684
- Extra tariff income (cash case only) = £0; net cash cost = £2,689,252

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 630 | 472 | £2,487,368 | £239,173 | £2,248,195 |
| 2 | 810 | 728 | £2,545,024 | £369,010 | £2,176,014 |
| 3 | 900 | 898 | £2,689,252 | £455,568 | £2,233,684 |
| 4 | 900 | 898 | £2,670,052 | £455,568 | £2,214,484 |
| 5 | 900 | 898 | £2,650,852 | £455,568 | £2,195,284 |
| Total | 4140 | 3895 | £13,042,548 | £1,974,886 | £11,067,661 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £10,039,666.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £3,150
- Extra cost per open operation avoided: £6,044
- Extra cost per bed-day released: £3,349
- Extra cost per serious event avoided: £147,748

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- 30-day benefit not yet modelled for Liver resection (22 cases a year), Oesophagogastric resection (22 cases a year), Pancreatoduodenectomy (Whipple's) (22 cases a year): their benefit is a zero placeholder pending evidence, not a finding that the robot has no benefit.
- 4 available sessions per fortnight left unfilled on the rota.
