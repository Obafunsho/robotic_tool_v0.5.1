# Worked example: Medium DGH (<800 beds), 1 robot, Platform B: established multi-port (purchase), central evidence
Engine version 0.7.0. All inputs are placeholders for expert review.

## Step 1 to 3. Two-week theatre template
Template: standard. Each robot has 14 days x 3 sessions (AM session 1, PM session 2, PM session 3), one procedure per session. Standard hours are weekday sessions 1 and 2 (Friday session 2 maintenance); session 3 and weekend sessions count only when used. Cases per session follow complexity: High 1, Medium 1.5, Low 3, whole day 0.5.
Booked sessions per fortnight = 18; available = 18; utilisation = 18 / 18 = 100%.
Annual cases = cases per fortnight x 22.5 fortnights x 100% going ahead; then limited to demand (check on). Above 700 per robot a year is flagged amber (advisory), not cut.

| Procedure | Cases per fortnight | On template (year) | Demand | Delivered | Unmet |
| --- | --- | --- | --- | --- | --- |
| Bariatric and anti-reflux surgery | 1.50 | 34 | 30 | 30 | 0 |
| Colectomy (right, left, sigmoid) | 3.00 | 68 | 72 | 68 | 4 |
| Complex abdominal wall repair | 4.00 | 90 | 80 | 80 | 0 |
| Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy) | 6.00 | 135 | 135 | 135 | 0 |
| Complex breast (mastectomy, flap reconstruction) | 0.00 | 0 | 20 | 0 | 20 |
| Complex cholecystectomy | 1.50 | 34 | 30 | 30 | 0 |
| Complex inguinal hernia | 0.00 | 0 | 40 | 0 | 40 |
| Gynaecological oncology (radical and cancer hysterectomy) | 2.00 | 45 | 30 | 30 | 0 |
| Nephrectomy (partial, radical, nephroureterectomy) | 3.00 | 68 | 50 | 50 | 0 |
| Rectal resection | 2.00 | 45 | 48 | 45 | 3 |

Cases per booked session by procedure: Bariatric and anti-reflux surgery 1.5; Colectomy 1.5; Complex abdominal wall repair 1; Complex benign gynaecology 1.5; Complex breast 1.5; Complex cholecystectomy 1.5; Complex inguinal hernia 3; Complex paediatric 1.5; Gynaecological oncology 1; Liver resection 0.5 (whole day); Lobectomy and transoral surgery 1; Nephrectomy 1.5; Oesophagogastric resection 0.5 (whole day); Pancreatoduodenectomy 0.5 (whole day); Radical cystectomy 0.5 (whole day); Radical prostatectomy 1; Rectal resection 1.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy)):

- Robotic cases = 135.0 x 1.00 = 135.0
- Without the robot, 47% would have open surgery = 63.0 cases; bed-days saved = 1.00 x 63.0 x 1.5 = 94.5; conversions avoided = 0.00; complications avoided = 1.70; returns to theatre avoided = 0.26
- Without the robot, 53% would have conventional minimal access (laparoscopic, endoscopic or laser) = 72.0 cases; bed-days saved = 1.00 x 72.0 x 0.2 = 14.4; conversions avoided = 2.43; complications avoided = 0.36; returns to theatre avoided = 0.00
- Group totals: bed-days 108.9, complications 2.06, returns to theatre 0.26, readmissions 0.32

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 467.5 |
| Open operations avoided | 164.8 |
| Bed-days released | 345.5 |
| Conversions avoided | 10.0 |
| Reoperations avoided | 1.4 |
| Major complications avoided | 6.1 |
| Readmissions avoided | 1.1 |
| Extra elective cases enabled | 86.4 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £274,286
- Platform public dividend capital: £43,200
- Platform maintenance: £150,000
- Instruments = 467.5 x £1,500 = £701,250
- Sterile services = 467.5 x £75 = £35,062
- Surgical first assistant = 1 x 1 WTE x £60,000 = £60,000
- Extra theatre time = 10459 min x £12 = £125,510
- Extra cost to the trust = £1,389,308 (£2,972 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £184,217
- Extra cost less cost avoided = £1,205,092
- Extra tariff income (cash case only) = £0; net cash cost = £1,389,308

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 327 | 181 | £1,274,962 | £96,714 | £1,178,248 |
| 2 | 421 | 280 | £1,312,726 | £149,216 | £1,163,511 |
| 3 | 468 | 346 | £1,389,308 | £184,217 | £1,205,092 |
| 4 | 468 | 346 | £1,379,708 | £184,217 | £1,195,492 |
| 5 | 468 | 346 | £1,370,108 | £184,217 | £1,185,892 |
| Total | 2150 | 1498 | £6,726,813 | £798,579 | £5,928,233 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £5,373,440.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £3,128
- Extra cost per open operation avoided: £8,876
- Extra cost per bed-day released: £4,491
- Extra cost per serious event avoided: £178,270

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- Colectomy (right, left, sigmoid): 4 cases a year are not scheduled (68 of 72 scheduled); the template does not schedule enough cases.
- Complex breast (mastectomy, flap reconstruction): 20 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Complex inguinal hernia: 40 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Gynaecological oncology (radical and cancer hysterectomy): the template schedules 45 cases a year but demand is 30, so its lists would be only 67% full.
- Nephrectomy (partial, radical, nephroureterectomy): the template schedules 68 cases a year but demand is 50, so its lists would be only 74% full.
- Rectal resection: 3 cases a year are not scheduled (45 of 48 scheduled); the template does not schedule enough cases.
- 30-day benefit not yet modelled for Complex cholecystectomy (30 cases a year): their benefit is a zero placeholder pending evidence, not a finding that the robot has no benefit.
