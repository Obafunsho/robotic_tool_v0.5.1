# Worked example: Large hospital (>=800 beds), 2 robots, Platform B: established multi-port (purchase), central evidence
Engine version 0.7.0. All inputs are placeholders for expert review.

## Step 1 to 3. Two-week theatre template
Template: standard. Each robot has 14 days x 3 sessions (AM session 1, PM session 2, PM session 3), one procedure per session. Standard hours are weekday sessions 1 and 2 (Friday session 2 maintenance); session 3 and weekend sessions count only when used. Cases per session follow complexity: High 1, Medium 1.5, Low 3, whole day 0.5.
Booked sessions per fortnight = 36; available = 36; utilisation = 36 / 36 = 100%.
Annual cases = cases per fortnight x 22.5 fortnights x 100% going ahead; then limited to demand (check on). Above 700 per robot a year is flagged amber (advisory), not cut.

| Procedure | Cases per fortnight | On template (year) | Demand | Delivered | Unmet |
| --- | --- | --- | --- | --- | --- |
| Bariatric and anti-reflux surgery | 0.00 | 0 | 60 | 0 | 60 |
| Colectomy (right, left, sigmoid) | 3.00 | 68 | 120 | 68 | 52 |
| Complex abdominal wall repair | 4.00 | 90 | 120 | 90 | 30 |
| Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy) | 7.50 | 169 | 210 | 169 | 41 |
| Complex breast (mastectomy, flap reconstruction) | 0.00 | 0 | 40 | 0 | 40 |
| Complex cholecystectomy | 0.00 | 0 | 50 | 0 | 50 |
| Complex inguinal hernia | 0.00 | 0 | 60 | 0 | 60 |
| Complex paediatric (pyeloplasty, fundoplication, choledochal cyst) | 0.00 | 0 | 50 | 0 | 50 |
| Gynaecological oncology (radical and cancer hysterectomy) | 1.00 | 22 | 50 | 22 | 28 |
| Liver resection | 1.00 | 22 | 40 | 22 | 18 |
| Lobectomy and transoral surgery | 0.00 | 0 | 40 | 0 | 40 |
| Nephrectomy (partial, radical, nephroureterectomy) | 4.50 | 101 | 120 | 101 | 19 |
| Oesophagogastric resection | 1.00 | 22 | 30 | 22 | 8 |
| Pancreatoduodenectomy (Whipple's) | 1.00 | 22 | 30 | 22 | 8 |
| Radical cystectomy | 1.00 | 22 | 50 | 22 | 28 |
| Radical prostatectomy | 10.00 | 225 | 250 | 225 | 25 |
| Rectal resection | 3.00 | 68 | 80 | 68 | 12 |

Cases per booked session by procedure: Bariatric and anti-reflux surgery 1.5; Colectomy 1.5; Complex abdominal wall repair 1; Complex benign gynaecology 1.5; Complex breast 1.5; Complex cholecystectomy 1.5; Complex inguinal hernia 3; Complex paediatric 1.5; Gynaecological oncology 1; Liver resection 0.5 (whole day); Lobectomy and transoral surgery 1; Nephrectomy 1.5; Oesophagogastric resection 0.5 (whole day); Pancreatoduodenectomy 0.5 (whole day); Radical cystectomy 0.5 (whole day); Radical prostatectomy 1; Rectal resection 1.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Radical prostatectomy):

- Robotic cases = 225.0 x 1.00 = 225.0
- Without the robot, 100% would have open surgery = 225.0 cases; bed-days saved = 1.00 x 225.0 x 2 = 450.0; conversions avoided = 0.00; complications avoided = 4.50; returns to theatre avoided = 1.12
- Without the robot, 0% would have conventional minimal access (laparoscopic, endoscopic or laser) = 0.0 cases; bed-days saved = 1.00 x 0.0 x 0.5 = 0.0; conversions avoided = 0.00; complications avoided = 0.00; returns to theatre avoided = 0.00
- Group totals: bed-days 450.0, complications 4.50, returns to theatre 1.12, readmissions 1.12

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 832.5 |
| Open operations avoided | 488.3 |
| Bed-days released | 913.2 |
| Conversions avoided | 12.2 |
| Reoperations avoided | 3.0 |
| Major complications avoided | 12.5 |
| Readmissions avoided | 2.5 |
| Extra elective cases enabled | 228.3 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £548,571
- Platform public dividend capital: £86,400
- Platform maintenance: £300,000
- Instruments = 832.5 x £1,500 = £1,248,750
- Sterile services = 832.5 x £75 = £62,438
- Surgical first assistant = 2 x 1 WTE x £60,000 = £120,000
- Extra theatre time = 13291 min x £12 = £159,498
- Extra cost to the trust = £2,525,657 (£3,034 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £451,888
- Extra cost less cost avoided = £2,073,768
- Extra tariff income (cash case only) = £0; net cash cost = £2,525,657

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 583 | 479 | £2,372,851 | £237,241 | £2,135,610 |
| 2 | 749 | 740 | £2,397,788 | £366,030 | £2,031,758 |
| 3 | 832 | 913 | £2,525,657 | £451,888 | £2,073,768 |
| 4 | 832 | 913 | £2,506,457 | £451,888 | £2,054,568 |
| 5 | 832 | 913 | £2,487,257 | £451,888 | £2,035,368 |
| Total | 3830 | 3959 | £12,290,009 | £1,958,936 | £10,331,073 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £9,377,987.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £3,209
- Extra cost per open operation avoided: £5,472
- Extra cost per bed-day released: £3,105
- Extra cost per serious event avoided: £157,384

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- Bariatric and anti-reflux surgery: 60 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Colectomy (right, left, sigmoid): 52 cases a year are not scheduled (68 of 120 scheduled); the template does not schedule enough cases.
- Complex abdominal wall repair: 30 cases a year are not scheduled (90 of 120 scheduled); the template does not schedule enough cases.
- Complex benign gynaecology (hysterectomy, myomectomy, endometriosis, sacrocolpopexy): 41 cases a year are not scheduled (169 of 210 scheduled); the template does not schedule enough cases.
- Complex breast (mastectomy, flap reconstruction): 40 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Complex cholecystectomy: 50 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Complex inguinal hernia: 60 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Complex paediatric (pyeloplasty, fundoplication, choledochal cyst): 50 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Gynaecological oncology (radical and cancer hysterectomy): 28 cases a year are not scheduled (22 of 50 scheduled); the template does not schedule enough cases.
- Liver resection: 18 cases a year are not scheduled (22 of 40 scheduled); the template does not schedule enough cases.
- Lobectomy and transoral surgery: 40 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Nephrectomy (partial, radical, nephroureterectomy): 19 cases a year are not scheduled (101 of 120 scheduled); the template does not schedule enough cases.
- Oesophagogastric resection: 8 cases a year are not scheduled (22 of 30 scheduled); the template does not schedule enough cases.
- Pancreatoduodenectomy (Whipple's): 8 cases a year are not scheduled (22 of 30 scheduled); the template does not schedule enough cases.
- Radical cystectomy: 28 cases a year are not scheduled (22 of 50 scheduled); the template does not schedule enough cases.
- Radical prostatectomy: 25 cases a year are not scheduled (225 of 250 scheduled); the template does not schedule enough cases.
- Rectal resection: 12 cases a year are not scheduled (68 of 80 scheduled); the template does not schedule enough cases.
- 30-day benefit not yet modelled for Liver resection (22 cases a year), Oesophagogastric resection (22 cases a year), Pancreatoduodenectomy (Whipple's) (22 cases a year): their benefit is a zero placeholder pending evidence, not a finding that the robot has no benefit.
