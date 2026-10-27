# Worked example: Large hospital (>=800 beds), 2 robots, Platform B: established multi-port (purchase), central evidence
Engine version 0.5.1. All inputs are placeholders for expert review.

## Step 1 to 3. Demand, capacity and plan
Capacity per fortnight = robots x sessions per week x 2 = 2 x 9 x 2 = 36.
Fortnights per year = 45 / 2 = 22.5.
A dedicated list is created only if it would be at least 75% full; leftover demand is pooled on shared half-day sessions, again only if they would be at least 75% full. Delivered cases are capped at 700 per robot per year.

| Group | Robotic cases available | Open without robot | Cases per list | List | Sessions/fortnight | Own lists | Shared list | Unmet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Colorectal major resection (colon and rectum) | 200 | 10% | 2 | all-day | 8 | 180 | 9 | 11 |
| Radical prostatectomy | 250 | 100% | 3 | all-day | 6 | 202 | 21 | 26 |
| Nephrectomy and partial nephrectomy | 120 | 30% | 3 | all-day | 4 | 120 | 0 | 0 |
| Radical cystectomy | 50 | 80% | 1 | all-day | 4 | 45 | 2 | 3 |
| Hysterectomy (benign and malignant) | 160 | 50% | 2 | half-day | 3 | 135 | 11 | 14 |
| Myomectomy | 40 | 80% | 1 | half-day | 2 | 40 | 0 | 0 |
| Endometriosis excision | 60 | 20% | 2 | all-day | 2 | 45 | 7 | 8 |
| Adnexal surgery | 50 | 10% | 3 | half-day | 0 | 0 | 22 | 28 |
| Abdominal wall (ventral and incisional hernia) | 120 | 70% | 2 | half-day | 2 | 90 | 14 | 16 |
| Paediatric (e.g. pyeloplasty, fundoplication) | 50 | 50% | 2 | half-day | 1 | 45 | 2 | 3 |
| Head and neck (transoral robotic surgery) | 40 | 80% | 3 | all-day | 0 | 0 | 18 | 22 |
| Upper GI (anti-reflux and hiatal hernia) | 40 | 5% | 2 | half-day | 1 | 40 | 0 | 0 |

Shared list: 3 half-day sessions per fortnight, 100% full.

Own-list cases = min(sessions x 22.5 x cases per list / sessions per list, cases available). Booked 36 of 36 sessions (100%). Robots needed to meet full demand: 2.16.

## Step 4 to 6. Patient consequences, year 3 (utilisation 100%, benefit multiplier 1.00)
Worked for one group (Radical prostatectomy):

- Robotic cases = 224 x 1.00 = 223.9
- Without the robot, 100% would have open surgery = 223.9 cases; bed-days saved = 1.00 x 223.9 x 2 = 447.8; conversions avoided = 0.00; complications avoided = 4.48; returns to theatre avoided = 1.12
- Without the robot, 0% would have conventional minimal access (laparoscopic, endoscopic or laser) = 0.0 cases; bed-days saved = 1.00 x 0.0 x 0.5 = 0.0; conversions avoided = 0.00; complications avoided = 0.00; returns to theatre avoided = 0.00
- Group totals: bed-days 447.8, complications 4.48, returns to theatre 1.12, readmissions 1.12

All groups combined:

| Consequence | Year 3 |
| --- | --- |
| Robotic cases | 1049.4 |
| Open operations avoided | 546.8 |
| Bed-days released | 1146.1 |
| Conversions avoided | 17.2 |
| Reoperations avoided | 3.8 |
| Major complications avoided | 16.3 |
| Readmissions avoided | 2.9 |
| Extra elective cases enabled | 286.5 |

## Step 7 to 9. Extra cost and cost avoided, year 3
- Platform depreciation: £548,571
- Platform public dividend capital: £86,400
- Platform maintenance: £300,000
- Instruments = 1049.4 x £1,500 = £1,574,062
- Sterile services = 1049.4 x £75 = £78,703
- Surgical first assistant = 2 x 1 WTE x £60,000 = £120,000
- Extra theatre time = 20437 min x £12 = £245,247
- Extra cost to the trust = £2,952,984 (£2,814 per case). Nothing is deducted for 30-day cost avoided.
- 30-day cost avoided (economic view, not cash) = bed-days x £400 + conversions x £1,000 + reoperations x £6,000 + complications x £4,000 + readmissions x £2,500 = £571,317
- Extra cost less cost avoided = £2,381,667

## Five-year view
| Year | Cases | Bed-days released | Extra cost | Cost avoided (not cash) | Extra cost less cost avoided |
| --- | --- | --- | --- | --- | --- |
| 1 | 735 | 602 | £2,671,980 | £299,942 | £2,372,039 |
| 2 | 944 | 928 | £2,782,383 | £462,767 | £2,319,616 |
| 3 | 1049 | 1146 | £2,952,984 | £571,317 | £2,381,667 |
| 4 | 1049 | 1146 | £2,933,784 | £571,317 | £2,362,467 |
| 5 | 1049 | 1146 | £2,914,584 | £571,317 | £2,343,267 |
| Total | 4827 | 4968 | £14,255,715 | £2,476,661 | £11,779,054 |

Economic case (discounted at 3.5%, capital in year 0, residual value credited in year 5): net present cost £10,680,403.

Cost per outcome (five-year extra cost divided by each consequence; not additive):

- Extra cost per robotic case: £2,953
- Extra cost per open operation avoided: £5,668
- Extra cost per bed-day released: £2,869
- Extra cost per serious event avoided: £142,378

Break-even: none. At this case mix each extra case adds more cost than it avoids at 30 days, so higher volume lowers the cost per case but never reaches break-even.

## Guardrail warnings
- Colorectal major resection (colon and rectum): 11 cases a year are not scheduled (189 of 200 scheduled); robot capacity is fully booked.
- Radical prostatectomy: 26 cases a year are not scheduled (224 of 250 scheduled); robot capacity is fully booked.
- Radical cystectomy: 3 cases a year are not scheduled (47 of 50 scheduled); robot capacity is fully booked.
- Hysterectomy (benign and malignant): 14 cases a year are not scheduled (146 of 160 scheduled); robot capacity is fully booked.
- Endometriosis excision: 8 cases a year are not scheduled (52 of 60 scheduled); robot capacity is fully booked.
- Adnexal surgery: 28 cases a year are not scheduled (22 of 50 scheduled); robot capacity is fully booked.
- Abdominal wall (ventral and incisional hernia): 16 cases a year are not scheduled (104 of 120 scheduled); robot capacity is fully booked.
- Paediatric (e.g. pyeloplasty, fundoplication): 3 cases a year are not scheduled (47 of 50 scheduled); robot capacity is fully booked.
- Head and neck (transoral robotic surgery): 22 cases a year are not scheduled (18 of 40 scheduled); robot capacity is fully booked.
