# Worked example: Large hospital (>=800 beds), 2 robots, Platform B: established multi-port (purchase), central evidence
Engine version 0.6.1. All inputs are placeholders for expert review.

## Step 1 to 3. Two-week theatre template
Template: standard. Each robot has 14 days x 3 sessions. Standard hours are weekday AM and PM (Friday PM maintenance); evening and weekend sessions count only when used.
Booked sessions per fortnight = 36; available = 36; utilisation = 36 / 36 = 100%.
Annual cases = cases per fortnight x 22.5 fortnights x 100% going ahead; then limited to demand (check on) and to 700 per robot.

| Procedure | Cases per fortnight | On template (year) | Demand | Delivered | Unmet |
| --- | --- | --- | --- | --- | --- |
| Colorectal major resection (colon and rectum) | 4.00 | 90 | 200 | 90 | 110 |
| Radical prostatectomy | 12.00 | 270 | 250 | 250 | 0 |
| Nephrectomy and partial nephrectomy | 6.00 | 135 | 120 | 120 | 0 |
| Radical cystectomy | 2.00 | 45 | 50 | 45 | 5 |
| Hysterectomy (benign and malignant) | 7.20 | 162 | 160 | 160 | 0 |
| Myomectomy | 1.80 | 41 | 40 | 40 | 0 |
| Endometriosis excision | 9.00 | 202 | 60 | 60 | 0 |
| Adnexal surgery | 3.00 | 68 | 50 | 50 | 0 |
| Abdominal wall reconstruction | 0.00 | 0 | 120 | 0 | 120 |
| Paediatric (e.g. pyeloplasty, fundoplication) | 3.00 | 68 | 50 | 50 | 0 |
| Head and neck (transoral robotic surgery) | 2.00 | 45 | 40 | 40 | 0 |
| Upper GI (anti-reflux and hiatal hernia) | 2.00 | 45 | 40 | 40 | 0 |

How tiers count (Appendix A of the business case): Colorectal major = Colorectal major resection (colon and rectum) 100%; Upper GI minor = Upper GI (anti-reflux and hiatal hernia) 100%; Abdominal wall major = Abdominal wall reconstruction 100%; Urology: prostate medium = Radical prostatectomy 100%; Urology: kidney medium = Nephrectomy and partial nephrectomy 100%; Urology: bladder medium = Radical cystectomy 100%; Gynaecology major = Hysterectomy (benign and malignant) 40%, Endometriosis excision 50%, Myomectomy 10%; Gynaecology minor = Adnexal surgery 100%; Paediatric major = Paediatric (e.g. pyeloplasty, fundoplication) 100%; Head and neck major = Head and neck (transoral robotic surgery) 100%.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Radical prostatectomy):

- Robotic cases = 250.0 x 1.00 = 250.0
- Without the robot, 100% would have open surgery = 250.0 cases; bed-days saved = 1.00 x 250.0 x 2 = 500.0; conversions avoided = 0.00; complications avoided = 5.00; returns to theatre avoided = 1.25
- Without the robot, 0% would have conventional minimal access (laparoscopic, endoscopic or laser) = 0.0 cases; bed-days saved = 1.00 x 0.0 x 0.5 = 0.0; conversions avoided = 0.00; complications avoided = 0.00; returns to theatre avoided = 0.00
- Group totals: bed-days 500.0, complications 5.00, returns to theatre 1.25, readmissions 1.25

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 945.0 |
| Open operations avoided | 519.0 |
| Bed-days released | 1088.0 |
| Conversions avoided | 12.8 |
| Reoperations avoided | 3.2 |
| Major complications avoided | 14.8 |
| Readmissions avoided | 2.5 |
| Extra elective cases enabled | 272.0 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £548,571
- Platform public dividend capital: £86,400
- Platform maintenance: £300,000
- Instruments = 945.0 x £1,500 = £1,417,500
- Sterile services = 945.0 x £75 = £70,875
- Surgical first assistant = 2 x 1 WTE x £60,000 = £120,000
- Extra theatre time = 15485 min x £12 = £185,820
- Extra cost to the trust = £2,729,166 (£2,888 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £532,510
- Extra cost less cost avoided = £2,196,656
- Extra tariff income (cash case only) = £0; net cash cost = £2,729,166

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 662 | 571 | £2,515,308 | £279,568 | £2,235,740 |
| 2 | 850 | 881 | £2,580,947 | £431,333 | £2,149,614 |
| 3 | 945 | 1088 | £2,729,166 | £532,510 | £2,196,656 |
| 4 | 945 | 1088 | £2,709,966 | £532,510 | £2,177,456 |
| 5 | 945 | 1088 | £2,690,766 | £532,510 | £2,158,256 |
| Total | 4347 | 4716 | £13,226,154 | £2,308,431 | £10,917,723 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £9,906,147.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £3,043
- Extra cost per open operation avoided: £5,540
- Extra cost per bed-day released: £2,804
- Extra cost per serious event avoided: £149,048

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- Colorectal major resection (colon and rectum): 110 cases a year are not scheduled (90 of 200 scheduled); the template does not schedule enough cases.
- Radical cystectomy: 5 cases a year are not scheduled (45 of 50 scheduled); the template does not schedule enough cases.
- Endometriosis excision: the template schedules 202 cases a year but demand is 60, so its lists would be only 30% full.
- Adnexal surgery: the template schedules 68 cases a year but demand is 50, so its lists would be only 74% full.
- Abdominal wall reconstruction: 120 cases a year are not scheduled (none scheduled); the template has no lists for it.
- Paediatric (e.g. pyeloplasty, fundoplication): the template schedules 68 cases a year but demand is 50, so its lists would be only 74% full.
- Gynaecology major cases: the template split (hysterectomy 40%, endometriosis excision 50%, myomectomy 10%) differs from the demand mix (hysterectomy 62%, endometriosis excision 23%, myomectomy 15%), so meeting demand for some procedures over-schedules others. Review the split in the advanced mapping table, or the demand.
