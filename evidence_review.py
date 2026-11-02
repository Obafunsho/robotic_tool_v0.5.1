"""
Clinical lead's literature review of the v0.7 assumptions register (October 2026),
applied as the v0.8 defaults. Generated from
assumptions_register_v0_7_0_literature_review.xlsx with these rules:

  - "change to" rows are applied, except the seven that increase length-of-stay benefit
    or the open share, which keep their v0.7 value (EXCLUDED_INCREASES)
  - complex cholecystectomy: every 30-day outcome effect set to zero, labelled
    "neutral (clinical lead)"; the 12 extra theatre minutes are kept
  - "agree" and "needs evidence" rows keep their v0.7 value
  - the citation in the reviewer's comment becomes the Source, and the evidence grade
    is assigned from the study design it names

Each entry: decision, v07 (value before review), proposed (reviewer's change),
value (value used from v0.8), source, grade, status, comment.
"""

EXCLUDED_INCREASES = ['abdo_wall_repair.los_reduction_open',
 'benign_gyn.los_reduction_open',
 'benign_gyn.p_open',
 'gyn_oncology.los_reduction_open',
 'gyn_oncology.p_open',
 'prostatectomy.los_reduction_open',
 'rectal.los_reduction_lap']

REVIEW = {'abdo_wall_repair.comp_reduction_lap': {'comment': 'Olavarria et al, BMJ 2020;370:m2457 (RCT; doi '
                                                    '10.1136/bmj.m2457): no complication benefit v '
                                                    'laparoscopic (2 enterotomies robotic v none). Indirect '
                                                    'evidence.',
                                         'decision': 'change to',
                                         'grade': 'Randomised trial',
                                         'proposed': 0.0,
                                         'source': 'Olavarria et al, BMJ 2020;370:m2457 (RCT; doi '
                                                   '10.1136/bmj.m2457): no complication benefit v '
                                                   'laparoscopic (2 enterotomies robotic v none). Indirect '
                                                   'evidence.',
                                         'status': 'Sourced',
                                         'v07': 0.005,
                                         'value': 0.0},
 'abdo_wall_repair.comp_reduction_open': {'comment': 'Lima et al, Surg Endosc 2024;38:7083-92 '
                                                     '(meta-analysis; doi 10.1007/s00464-024-11382-w): '
                                                     'overall complications 9.0% v 24.6% (RR 0.43); surgical '
                                                     'site occurrence needing intervention 5.4% v 8.9% (not '
                                                     'significant). 4 points for major complications is '
                                                     'moderate (observational).',
                                          'decision': 'change to',
                                          'grade': 'Meta-analysis',
                                          'proposed': 0.04,
                                          'source': 'Lima et al, Surg Endosc 2024;38:7083-92 (meta-analysis; '
                                                    'doi 10.1007/s00464-024-11382-w): overall complications '
                                                    '9.0% v 24.6% (RR 0.43); surgical site occurrence '
                                                    'needing intervention 5.4% v 8.9% (not significant). 4 '
                                                    'points for major complications is moderate '
                                                    '(observational).',
                                          'status': 'Sourced',
                                          'v07': 0.03,
                                          'value': 0.04},
 'abdo_wall_repair.conv_reduction_lap': {'comment': 'No robotic v laparoscopic complex repair data. Note '
                                                    'that robotic TAR itself converts to open in 6.4% (Lima '
                                                    'et al, Surg Endosc 2024;38:7083-92 (meta-analysis; doi '
                                                    '10.1007/s00464-024-11382-w)), which the model does not '
                                                    'count.',
                                         'decision': 'needs evidence',
                                         'grade': 'Meta-analysis',
                                         'proposed': None,
                                         'source': 'No robotic v laparoscopic complex repair data. Note that '
                                                   'robotic TAR itself converts to open in 6.4% (Lima et al, '
                                                   'Surg Endosc 2024;38:7083-92 (meta-analysis; doi '
                                                   '10.1007/s00464-024-11382-w)), which the model does not '
                                                   'count.',
                                         'status': 'Needs evidence',
                                         'v07': 0.02,
                                         'value': 0.02},
 'abdo_wall_repair.extra_minutes_lap': {'comment': 'Olavarria et al, BMJ 2020;370:m2457 (RCT; doi '
                                                   '10.1136/bmj.m2457): 141 v 77 min (MD +63). Indirect '
                                                   '(non-complex hernias).',
                                        'decision': 'change to',
                                        'grade': 'Randomised trial',
                                        'proposed': 60.0,
                                        'source': 'Olavarria et al, BMJ 2020;370:m2457 (RCT; doi '
                                                  '10.1136/bmj.m2457): 141 v 77 min (MD +63). Indirect '
                                                  '(non-complex hernias).',
                                        'status': 'Sourced',
                                        'v07': 30.0,
                                        'value': 60.0},
 'abdo_wall_repair.extra_minutes_open': {'comment': 'Lima et al, Surg Endosc 2024;38:7083-92 (meta-analysis; '
                                                    'doi 10.1007/s00464-024-11382-w): open operative time '
                                                    'shorter by 67.7 min.',
                                         'decision': 'change to',
                                         'grade': 'Meta-analysis',
                                         'proposed': 68.0,
                                         'source': 'Lima et al, Surg Endosc 2024;38:7083-92 (meta-analysis; '
                                                   'doi 10.1007/s00464-024-11382-w): open operative time '
                                                   'shorter by 67.7 min.',
                                         'status': 'Sourced',
                                         'v07': 45.0,
                                         'value': 68.0},
 'abdo_wall_repair.los_reduction_lap': {'comment': 'Olavarria et al, BMJ 2020;370:m2457 (RCT; doi '
                                                   '10.1136/bmj.m2457): no difference in hospital days v '
                                                   'laparoscopic (median 0 v 0). Indirect evidence '
                                                   '(non-complex hernias).',
                                        'decision': 'change to',
                                        'grade': 'Randomised trial',
                                        'proposed': 0.0,
                                        'source': 'Olavarria et al, BMJ 2020;370:m2457 (RCT; doi '
                                                  '10.1136/bmj.m2457): no difference in hospital days v '
                                                  'laparoscopic (median 0 v 0). Indirect evidence '
                                                  '(non-complex hernias).',
                                        'status': 'Sourced',
                                        'v07': 0.2,
                                        'value': 0.0},
 'abdo_wall_repair.los_reduction_open': {'comment': 'Lima et al, Surg Endosc 2024;38:7083-92 (meta-analysis; '
                                                    'doi 10.1007/s00464-024-11382-w) (7 observational '
                                                    'studies, 780 patients): robotic TAR stay -3.9 days '
                                                    '(-4.8 to -3.1); Dewulf et al, BJS Open 2022;6:zrac057 '
                                                    '(two European centres): 3.4 v 6.9 days. 3.0 allows for '
                                                    'selection bias.',
                                         'decision': 'change to',
                                         'grade': 'Meta-analysis',
                                         'proposed': 3.0,
                                         'source': 'Clinical lead kept the v0.7 value (1.5); the literature '
                                                   'review proposed 3, but the evidence is not yet '
                                                   'considered reliable enough for bed-days or the open '
                                                   'share. Review: Lima et al, Surg Endosc 2024;38:7083-92 '
                                                   '(meta-analysis; doi 10.1007/s00464-024-11382-w) (7 '
                                                   'observational studies, 780 patients): robotic TAR stay '
                                                   '-3.9 days (-4.8 to -3.1); Dewulf et al, BJS Open '
                                                   '2022;6:zrac057 (two European centres): 3.4 v 6.9 days. '
                                                   '3.0 allows for selection bias.',
                                         'status': 'Clinical lead input',
                                         'v07': 1.5,
                                         'value': 1.5},
 'abdo_wall_repair.p_open': {'comment': 'Consistent with clinical lead opinion that the comparator is mostly '
                                        'open and with the national context figure.',
                             'decision': 'agree',
                             'grade': 'Clinical lead opinion',
                             'proposed': None,
                             'source': 'Consistent with clinical lead opinion that the comparator is mostly '
                                       'open and with the national context figure.',
                             'status': 'Clinical lead input',
                             'v07': 0.7,
                             'value': 0.7},
 'abdo_wall_repair.readm_reduction_lap': {'comment': 'No evidence of a difference. Retain zero.',
                                          'decision': 'agree',
                                          'grade': 'None',
                                          'proposed': None,
                                          'source': 'No evidence of a difference. Retain zero.',
                                          'status': 'Clinical lead input',
                                          'v07': 0.0,
                                          'value': 0.0},
 'abdo_wall_repair.readm_reduction_open': {'comment': 'Evidence mixed: Lima et al, Surg Endosc '
                                                      '2024;38:7083-92 (meta-analysis; doi '
                                                      '10.1007/s00464-024-11382-w) no readmission '
                                                      'difference; Tran et al, ANZ J Surg 2024;94:37-46 (doi '
                                                      '10.1111/ans.18822) fewer readmissions. Retain 1%.',
                                           'decision': 'agree',
                                           'grade': 'Meta-analysis',
                                           'proposed': None,
                                           'source': 'Evidence mixed: Lima et al, Surg Endosc '
                                                     '2024;38:7083-92 (meta-analysis; doi '
                                                     '10.1007/s00464-024-11382-w) no readmission difference; '
                                                     'Tran et al, ANZ J Surg 2024;94:37-46 (doi '
                                                     '10.1111/ans.18822) fewer readmissions. Retain 1%.',
                                           'status': 'Sourced',
                                           'v07': 0.01,
                                           'value': 0.01},
 'abdo_wall_repair.reop_reduction_lap': {'comment': 'No evidence of a difference. Retain zero.',
                                         'decision': 'agree',
                                         'grade': 'None',
                                         'proposed': None,
                                         'source': 'No evidence of a difference. Retain zero.',
                                         'status': 'Clinical lead input',
                                         'v07': 0.0,
                                         'value': 0.0},
 'abdo_wall_repair.reop_reduction_open': {'comment': 'Consistent with fewer site occurrences needing '
                                                     'intervention (Lima et al, Surg Endosc 2024;38:7083-92 '
                                                     '(meta-analysis; doi 10.1007/s00464-024-11382-w)). '
                                                     'Retain 0.5%.',
                                          'decision': 'agree',
                                          'grade': 'Meta-analysis',
                                          'proposed': None,
                                          'source': 'Consistent with fewer site occurrences needing '
                                                    'intervention (Lima et al, Surg Endosc 2024;38:7083-92 '
                                                    '(meta-analysis; doi 10.1007/s00464-024-11382-w)). '
                                                    'Retain 0.5%.',
                                          'status': 'Sourced',
                                          'v07': 0.005,
                                          'value': 0.005},
 'benign_gyn.comp_reduction_lap': {'comment': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                              '10.1002/14651858.CD011422.pub2; PMID 30985921): little or no '
                                              'difference in complications robotic v laparoscopic (low '
                                              'certainty).',
                                   'decision': 'change to',
                                   'grade': 'Cochrane systematic review',
                                   'proposed': 0.0,
                                   'source': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                             '10.1002/14651858.CD011422.pub2; PMID 30985921): little or no '
                                             'difference in complications robotic v laparoscopic (low '
                                             'certainty).',
                                   'status': 'Sourced',
                                   'v07': 0.005,
                                   'value': 0.0},
 'benign_gyn.comp_reduction_open': {'comment': 'Cochrane 2023 (Pickett et al): laparoscopic v abdominal '
                                               'fewer wound and abdominal wall infections but more urinary '
                                               'tract injuries. Retain 2.7%.',
                                    'decision': 'agree',
                                    'grade': 'Cochrane systematic review',
                                    'proposed': None,
                                    'source': 'Cochrane 2023 (Pickett et al): laparoscopic v abdominal fewer '
                                              'wound and abdominal wall infections but more urinary tract '
                                              'injuries. Retain 2.7%.',
                                    'status': 'Sourced',
                                    'v07': 0.027000000000000003,
                                    'value': 0.027000000000000003},
 'benign_gyn.conv_reduction_lap': {'comment': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                              '10.1002/14651858.CD011422.pub2; PMID 30985921): little or no '
                                              'difference in conversion, robotic v laparoscopic benign '
                                              'hysterectomy (low certainty). 3.4% not supported; 1.0 kept '
                                              'for complex cases (judgement).',
                                   'decision': 'change to',
                                   'grade': 'Cochrane systematic review',
                                   'proposed': 0.01,
                                   'source': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                             '10.1002/14651858.CD011422.pub2; PMID 30985921): little or no '
                                             'difference in conversion, robotic v laparoscopic benign '
                                             'hysterectomy (low certainty). 3.4% not supported; 1.0 kept for '
                                             'complex cases (judgement).',
                                   'status': 'Sourced',
                                   'v07': 0.034,
                                   'value': 0.01},
 'benign_gyn.extra_minutes_lap': {'comment': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                             '10.1002/14651858.CD011422.pub2; PMID 30985921): robot-assisted '
                                             'hysterectomy about 40 min longer than conventional in two '
                                             'trials.',
                                  'decision': 'change to',
                                  'grade': 'Cochrane systematic review',
                                  'proposed': 40.0,
                                  'source': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                            '10.1002/14651858.CD011422.pub2; PMID 30985921): robot-assisted '
                                            'hysterectomy about 40 min longer than conventional in two '
                                            'trials.',
                                  'status': 'Sourced',
                                  'v07': 20.0,
                                  'value': 40.0},
 'benign_gyn.extra_minutes_open': {'comment': 'No robotic v open benign operating-time estimate extracted.',
                                   'decision': 'needs evidence',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No robotic v open benign operating-time estimate extracted.',
                                   'status': 'Needs evidence',
                                   'v07': 21.8519,
                                   'value': 21.8519},
 'benign_gyn.los_reduction_lap': {'comment': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                             '10.1002/14651858.CD011422.pub2; PMID 30985921): robotic v '
                                             'laparoscopic stay MD -0.30 to +0.26 days, very low certainty. '
                                             'Retain 0.2.',
                                  'decision': 'agree',
                                  'grade': 'Cochrane systematic review',
                                  'proposed': None,
                                  'source': 'Lawrie et al, Cochrane CD011422.pub2, 2019 (doi '
                                            '10.1002/14651858.CD011422.pub2; PMID 30985921): robotic v '
                                            'laparoscopic stay MD -0.30 to +0.26 days, very low certainty. '
                                            'Retain 0.2.',
                                  'status': 'Sourced',
                                  'v07': 0.2,
                                  'value': 0.2},
 'benign_gyn.los_reduction_open': {'comment': 'Nieboer et al, Cochrane CD003677.pub4, 2009: laparoscopic v '
                                              'abdominal hysterectomy stay MD 2.0 days shorter; 2023 update '
                                              '(Pickett et al, CD003677.pub6, PMID 37642285) confirms '
                                              'shorter stay. Robot assumed equivalent to laparoscopy (Lawrie '
                                              'et al, Cochrane CD011422.pub2, 2019 (doi '
                                              '10.1002/14651858.CD011422.pub2; PMID 30985921)).',
                                   'decision': 'change to',
                                   'grade': 'Cochrane systematic review',
                                   'proposed': 2.0,
                                   'source': 'Clinical lead kept the v0.7 value (1.5); the literature review '
                                             'proposed 2, but the evidence is not yet considered reliable '
                                             'enough for bed-days or the open share. Review: Nieboer et al, '
                                             'Cochrane CD003677.pub4, 2009: laparoscopic v abdominal '
                                             'hysterectomy stay MD 2.0 days shorter; 2023 update (Pickett et '
                                             'al, CD003677.pub6, PMID 37642285) confirms shorter stay. Robot '
                                             'assumed equivalent to laparoscopy (Lawrie et al, Cochrane '
                                             'CD011422.pub2, 2019 (doi 10.1002/14651858.CD011422.pub2; PMID '
                                             '30985921)).',
                                   'status': 'Clinical lead input',
                                   'v07': 1.5,
                                   'value': 1.5},
 'benign_gyn.p_open': {'comment': 'Clinical lead opinion: complex benign cases (large uteri, deep '
                                  'endometriosis) are compared mainly with open surgery. Madhvani data '
                                  '(about half laparoscopic) cover all benign hysterectomies; no source for '
                                  'the complex subgroup.',
                       'decision': 'change to',
                       'grade': 'Clinical lead opinion',
                       'proposed': 0.6,
                       'source': 'Clinical lead kept the v0.7 value (47%); the literature review proposed '
                                 '0.6, but the evidence is not yet considered reliable enough for bed-days '
                                 'or the open share. Review: Clinical lead opinion: complex benign cases '
                                 '(large uteri, deep endometriosis) are compared mainly with open surgery. '
                                 'Madhvani data (about half laparoscopic) cover all benign hysterectomies; '
                                 'no source for the complex subgroup.',
                       'status': 'Clinical lead input',
                       'v07': 0.47,
                       'value': 0.47},
 'benign_gyn.readm_reduction_lap': {'comment': 'No evidence of a difference. Retain zero.',
                                    'decision': 'agree',
                                    'grade': 'None',
                                    'proposed': None,
                                    'source': 'No evidence of a difference. Retain zero.',
                                    'status': 'Clinical lead input',
                                    'v07': 0.0,
                                    'value': 0.0},
 'benign_gyn.readm_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                                'review; value retained as placeholder.',
                                     'decision': 'needs evidence',
                                     'grade': 'None',
                                     'proposed': None,
                                     'source': 'No robotic v open comparative evidence identified in this '
                                               'review; value retained as placeholder.',
                                     'status': 'Needs evidence',
                                     'v07': 0.005,
                                     'value': 0.005},
 'benign_gyn.reop_reduction_lap': {'comment': 'No evidence of a difference. Retain zero.',
                                   'decision': 'agree',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No evidence of a difference. Retain zero.',
                                   'status': 'Clinical lead input',
                                   'v07': 0.0,
                                   'value': 0.0},
 'benign_gyn.reop_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                               'review; value retained as placeholder.',
                                    'decision': 'needs evidence',
                                    'grade': 'None',
                                    'proposed': None,
                                    'source': 'No robotic v open comparative evidence identified in this '
                                              'review; value retained as placeholder.',
                                    'status': 'Needs evidence',
                                    'v07': 0.004,
                                    'value': 0.004},
 'cholecystectomy.comp_reduction_lap': {'comment': 'Woldehana et al, JAMA Surg 2025;160:755-62 (doi '
                                                   '10.1001/jamasurg.2025.1291; PMID 40397430): major '
                                                   'complications higher with robot (OR 1.57). Fewer '
                                                   'complications not supported; retain zero.',
                                        'decision': 'agree',
                                        'grade': 'Clinical lead opinion',
                                        'proposed': None,
                                        'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                  'Literature review: Woldehana et al, JAMA Surg '
                                                  '2025;160:755-62 (doi 10.1001/jamasurg.2025.1291; PMID '
                                                  '40397430): major complications higher with robot (OR '
                                                  '1.57). Fewer complications not supported; retain zero.',
                                        'status': 'Neutral (clinical lead)',
                                        'v07': 0.0,
                                        'value': 0.0},
 'cholecystectomy.comp_reduction_open': {'comment': 'No robotic v open comparative evidence identified in '
                                                    'this review; value retained as placeholder.',
                                         'decision': 'needs evidence',
                                         'grade': 'Clinical lead opinion',
                                         'proposed': None,
                                         'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                   'Literature review: No robotic v open comparative '
                                                   'evidence identified in this review; value retained as '
                                                   'placeholder.',
                                         'status': 'Neutral (clinical lead)',
                                         'v07': 0.0,
                                         'value': 0.0},
 'cholecystectomy.conv_reduction_lap': {'comment': 'Campbell et al, World J Emerg Surg 2023;18:55 (doi '
                                                   '10.1186/s13017-023-00521-8; matched urgent cohort): '
                                                   'conversion 1.9% v 3.2%. Ciocan et al, Medicina '
                                                   '2026;62:2070 (systematic review; doi '
                                                   '10.3390/medicina62112070): fewer conversions in most '
                                                   'studies; risk of bias serious.',
                                        'decision': 'change to',
                                        'grade': 'Clinical lead opinion',
                                        'proposed': 0.013,
                                        'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                  'Literature review: Campbell et al, World J Emerg Surg '
                                                  '2023;18:55 (doi 10.1186/s13017-023-00521-8; matched '
                                                  'urgent cohort): conversion 1.9% v 3.2%. Ciocan et al, '
                                                  'Medicina 2026;62:2070 (systematic review; doi '
                                                  '10.3390/medicina62112070): fewer conversions in most '
                                                  'studies; risk of bias serious.',
                                        'status': 'Neutral (clinical lead)',
                                        'v07': 0.0,
                                        'value': 0.0},
 'cholecystectomy.extra_minutes_lap': {'comment': 'Ciocan et al, Medicina 2026;62:2070 (systematic review; '
                                                  'doi 10.3390/medicina62112070), summarising meta-analyses '
                                                  '(eg Delgado et al, J Robot Surg 2024;18:242, doi '
                                                  '10.1007/s11701-024-01989-5): robotic cholecystectomy '
                                                  'about 12-13 min longer.',
                                       'decision': 'change to',
                                       'grade': 'Systematic review',
                                       'proposed': 12.0,
                                       'source': 'Ciocan et al, Medicina 2026;62:2070 (systematic review; '
                                                 'doi 10.3390/medicina62112070), summarising meta-analyses '
                                                 '(eg Delgado et al, J Robot Surg 2024;18:242, doi '
                                                 '10.1007/s11701-024-01989-5): robotic cholecystectomy about '
                                                 '12-13 min longer.',
                                       'status': 'Sourced',
                                       'v07': 0.0,
                                       'value': 12.0},
 'cholecystectomy.extra_minutes_open': {'comment': 'No robotic v open comparative evidence identified in '
                                                   'this review; value retained as placeholder.',
                                        'decision': 'needs evidence',
                                        'grade': 'None',
                                        'proposed': None,
                                        'source': 'No robotic v open comparative evidence identified in this '
                                                  'review; value retained as placeholder.',
                                        'status': 'Needs evidence',
                                        'v07': 0.0,
                                        'value': 0.0},
 'cholecystectomy.los_reduction_lap': {'comment': 'Woldehana et al, JAMA Surg 2025;160:755-62 (doi '
                                                  '10.1001/jamasurg.2025.1291; PMID 40397430) (70,074 '
                                                  'matched acute-care cases): stay longer with robot (median '
                                                  '3 v 2 days; MD +0.15 days). Shorter stay not supported, '
                                                  "so the clinical lead's direction is not adopted here.",
                                       'decision': 'agree',
                                       'grade': 'Clinical lead opinion',
                                       'proposed': None,
                                       'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                 'Literature review: Woldehana et al, JAMA Surg '
                                                 '2025;160:755-62 (doi 10.1001/jamasurg.2025.1291; PMID '
                                                 '40397430) (70,074 matched acute-care cases): stay longer '
                                                 'with robot (median 3 v 2 days; MD +0.15 days). Shorter '
                                                 "stay not supported, so the clinical lead's direction is "
                                                 'not adopted here.',
                                       'status': 'Neutral (clinical lead)',
                                       'v07': 0.0,
                                       'value': 0.0},
 'cholecystectomy.los_reduction_open': {'comment': 'No robotic v open comparative evidence identified in '
                                                   'this review; value retained as placeholder.',
                                        'decision': 'needs evidence',
                                        'grade': 'Clinical lead opinion',
                                        'proposed': None,
                                        'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                  'Literature review: No robotic v open comparative evidence '
                                                  'identified in this review; value retained as placeholder.',
                                        'status': 'Neutral (clinical lead)',
                                        'v07': 0.0,
                                        'value': 0.0},
 'cholecystectomy.p_open': {'comment': 'No source for the open share of complex cholecystectomy in England. '
                                       'Retain 10% pending data.',
                            'decision': 'needs evidence',
                            'grade': 'None',
                            'proposed': None,
                            'source': 'No source for the open share of complex cholecystectomy in England. '
                                      'Retain 10% pending data.',
                            'status': 'Needs evidence',
                            'v07': 0.1,
                            'value': 0.1},
 'cholecystectomy.readm_reduction_lap': {'comment': 'No evidence of a readmission benefit. Retain zero.',
                                         'decision': 'agree',
                                         'grade': 'Clinical lead opinion',
                                         'proposed': None,
                                         'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                   'Literature review: No evidence of a readmission benefit. '
                                                   'Retain zero.',
                                         'status': 'Neutral (clinical lead)',
                                         'v07': 0.0,
                                         'value': 0.0},
 'cholecystectomy.readm_reduction_open': {'comment': 'No robotic v open comparative evidence identified in '
                                                     'this review; value retained as placeholder.',
                                          'decision': 'needs evidence',
                                          'grade': 'Clinical lead opinion',
                                          'proposed': None,
                                          'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                    'Literature review: No robotic v open comparative '
                                                    'evidence identified in this review; value retained as '
                                                    'placeholder.',
                                          'status': 'Neutral (clinical lead)',
                                          'v07': 0.0,
                                          'value': 0.0},
 'cholecystectomy.reop_reduction_lap': {'comment': 'Coded bile duct injury equivalent (Woldehana et al, JAMA '
                                                   'Surg 2025;160:755-62 (doi 10.1001/jamasurg.2025.1291; '
                                                   'PMID 40397430): 0.37% v 0.39%). Ciocan et al, Medicina '
                                                   '2026;62:2070 (systematic review; doi '
                                                   '10.3390/medicina62112070): evidence neither shows nor '
                                                   'excludes a difference in major injury (Medicare repair '
                                                   'data RR 3.16). Zero reflects equivalence; keep Kalata '
                                                   '2023 as a caveat.',
                                        'decision': 'agree',
                                        'grade': 'Clinical lead opinion',
                                        'proposed': None,
                                        'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                  'Literature review: Coded bile duct injury equivalent '
                                                  '(Woldehana et al, JAMA Surg 2025;160:755-62 (doi '
                                                  '10.1001/jamasurg.2025.1291; PMID 40397430): 0.37% v '
                                                  '0.39%). Ciocan et al, Medicina 2026;62:2070 (systematic '
                                                  'review; doi 10.3390/medicina62112070): evidence neither '
                                                  'shows nor excludes a difference in major injury (Medicare '
                                                  'repair data RR 3.16). Zero reflects equivalence; keep '
                                                  'Kalata 2023 as a caveat.',
                                        'status': 'Neutral (clinical lead)',
                                        'v07': 0.0,
                                        'value': 0.0},
 'cholecystectomy.reop_reduction_open': {'comment': 'No robotic v open comparative evidence identified in '
                                                    'this review; value retained as placeholder.',
                                         'decision': 'needs evidence',
                                         'grade': 'Clinical lead opinion',
                                         'proposed': None,
                                         'source': 'Clinical lead: 30-day effect set to neutral (zero). '
                                                   'Literature review: No robotic v open comparative '
                                                   'evidence identified in this review; value retained as '
                                                   'placeholder.',
                                         'status': 'Neutral (clinical lead)',
                                         'v07': 0.0,
                                         'value': 0.0},
 'colectomy.comp_reduction_lap': {'comment': 'Cuk et al, Surg Endosc 2022 (meta-analysis, 20 studies; doi '
                                             '10.1007/s00464-021-08782-7; PMID 34724576): anastomotic leak '
                                             'OR 0.54 (0.32-0.94); overall complications OR 0.85 '
                                             '(0.73-1.00); GRADE very low. On an assumed laparoscopic leak '
                                             'risk of about 3% (modelling assumption) this gives about 1.4 '
                                             'points; 1.0 used because certainty is very low.',
                                  'decision': 'change to',
                                  'grade': 'Meta-analysis',
                                  'proposed': 0.01,
                                  'source': 'Cuk et al, Surg Endosc 2022 (meta-analysis, 20 studies; doi '
                                            '10.1007/s00464-021-08782-7; PMID 34724576): anastomotic leak OR '
                                            '0.54 (0.32-0.94); overall complications OR 0.85 (0.73-1.00); '
                                            'GRADE very low. On an assumed laparoscopic leak risk of about '
                                            '3% (modelling assumption) this gives about 1.4 points; 1.0 used '
                                            'because certainty is very low.',
                                  'status': 'Sourced',
                                  'v07': 0.005,
                                  'value': 0.01},
 'colectomy.comp_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                              'review; value retained as placeholder.',
                                   'decision': 'needs evidence',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No robotic v open comparative evidence identified in this '
                                             'review; value retained as placeholder.',
                                   'status': 'Needs evidence',
                                   'v07': 0.04,
                                   'value': 0.04},
 'colectomy.conv_reduction_lap': {'comment': 'Cuk et al, Surg Endosc 2022 (meta-analysis, 20 studies; doi '
                                             '10.1007/s00464-021-08782-7; PMID 34724576): conversion OR 0.31 '
                                             '(0.23-0.41), GRADE very low; US registry 9.8% v 4.8% (Surg '
                                             'Endosc 2024, doi 10.1007/s00464-024-11079-0). Supports about 5 '
                                             "percentage points; consistent with 'slightly lower "
                                             "conversion'.",
                                  'decision': 'agree',
                                  'grade': 'Meta-analysis',
                                  'proposed': None,
                                  'source': 'Cuk et al, Surg Endosc 2022 (meta-analysis, 20 studies; doi '
                                            '10.1007/s00464-021-08782-7; PMID 34724576): conversion OR 0.31 '
                                            '(0.23-0.41), GRADE very low; US registry 9.8% v 4.8% (Surg '
                                            'Endosc 2024, doi 10.1007/s00464-024-11079-0). Supports about 5 '
                                            "percentage points; consistent with 'slightly lower conversion'.",
                                  'status': 'Sourced',
                                  'v07': 0.05,
                                  'value': 0.05},
 'colectomy.extra_minutes_lap': {'comment': 'Cuk et al, Surg Endosc 2022 (meta-analysis, 20 studies; doi '
                                            '10.1007/s00464-021-08782-7; PMID 34724576): operative time MD '
                                            '+43 min (28-58). Current 20 understates theatre cost.',
                                 'decision': 'change to',
                                 'grade': 'Meta-analysis',
                                 'proposed': 40.0,
                                 'source': 'Cuk et al, Surg Endosc 2022 (meta-analysis, 20 studies; doi '
                                           '10.1007/s00464-021-08782-7; PMID 34724576): operative time MD '
                                           '+43 min (28-58). Current 20 understates theatre cost.',
                                 'status': 'Sourced',
                                 'v07': 20.0,
                                 'value': 40.0},
 'colectomy.extra_minutes_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                             'review; value retained as placeholder.',
                                  'decision': 'needs evidence',
                                  'grade': 'None',
                                  'proposed': None,
                                  'source': 'No robotic v open comparative evidence identified in this '
                                            'review; value retained as placeholder.',
                                  'status': 'Needs evidence',
                                  'v07': 30.0,
                                  'value': 30.0},
 'colectomy.los_reduction_lap': {'comment': 'Trastulli et al, PLoS One 2015 (doi '
                                            '10.1371/journal.pone.0134062): MD -0.68 days, mostly '
                                            'observational; Cuk et al, Surg Endosc 2022 (meta-analysis, 20 '
                                            'studies; doi 10.1007/s00464-021-08782-7; PMID 34724576) '
                                            'reported no significant stay benefit. 0.5 days already matches '
                                            'the evidence; a larger value is not supported.',
                                 'decision': 'agree',
                                 'grade': 'Meta-analysis',
                                 'proposed': None,
                                 'source': 'Trastulli et al, PLoS One 2015 (doi '
                                           '10.1371/journal.pone.0134062): MD -0.68 days, mostly '
                                           'observational; Cuk et al, Surg Endosc 2022 (meta-analysis, 20 '
                                           'studies; doi 10.1007/s00464-021-08782-7; PMID 34724576) reported '
                                           'no significant stay benefit. 0.5 days already matches the '
                                           'evidence; a larger value is not supported.',
                                 'status': 'Sourced',
                                 'v07': 0.5,
                                 'value': 0.5},
 'colectomy.los_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                             'review; value retained as placeholder.',
                                  'decision': 'needs evidence',
                                  'grade': 'None',
                                  'proposed': None,
                                  'source': 'No robotic v open comparative evidence identified in this '
                                            'review; value retained as placeholder.',
                                  'status': 'Needs evidence',
                                  'v07': 2.0,
                                  'value': 2.0},
 'colectomy.p_open': {'comment': 'No source for the share of robotic candidates who would otherwise be open. '
                                 'NBOCA 2025 (25% open) covers all major resections incl. emergencies, so it '
                                 'is context only. Retain 10% pending local data.',
                      'decision': 'needs evidence',
                      'grade': 'None',
                      'proposed': None,
                      'source': 'No source for the share of robotic candidates who would otherwise be open. '
                                'NBOCA 2025 (25% open) covers all major resections incl. emergencies, so it '
                                'is context only. Retain 10% pending local data.',
                      'status': 'Needs evidence',
                      'v07': 0.1,
                      'value': 0.1},
 'colectomy.readm_reduction_lap': {'comment': 'No evidence of a readmission difference identified. Retain '
                                              'zero.',
                                   'decision': 'agree',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No evidence of a readmission difference identified. Retain '
                                             'zero.',
                                   'status': 'Clinical lead input',
                                   'v07': 0.0,
                                   'value': 0.0},
 'colectomy.readm_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                               'review; value retained as placeholder.',
                                    'decision': 'needs evidence',
                                    'grade': 'None',
                                    'proposed': None,
                                    'source': 'No robotic v open comparative evidence identified in this '
                                              'review; value retained as placeholder.',
                                    'status': 'Needs evidence',
                                    'v07': 0.01,
                                    'value': 0.01},
 'colectomy.reop_reduction_lap': {'comment': 'No pooled estimate of reoperation identified; small value '
                                             'consistent with the leak reduction above. Retain.',
                                  'decision': 'agree',
                                  'grade': 'None',
                                  'proposed': None,
                                  'source': 'No pooled estimate of reoperation identified; small value '
                                            'consistent with the leak reduction above. Retain.',
                                  'status': 'Clinical lead input',
                                  'v07': 0.005,
                                  'value': 0.005},
 'colectomy.reop_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                              'review; value retained as placeholder.',
                                   'decision': 'needs evidence',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No robotic v open comparative evidence identified in this '
                                             'review; value retained as placeholder.',
                                   'status': 'Needs evidence',
                                   'v07': 0.02,
                                   'value': 0.02},
 'cystectomy.comp_reduction_lap': {'comment': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                   'decision': 'needs evidence',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                   'status': 'Needs evidence',
                                   'v07': 0.01,
                                   'value': 0.01},
 'cystectomy.comp_reduction_open': {'comment': 'Catto et al (iROC RCT, 9 UK centres), JAMA 2022;327:2092-103 '
                                               '(doi 10.1001/jama.2022.7393): overall complications similar '
                                               '(63.4% v 67.9%), but thromboembolic 1.9% v 8.3% and wound '
                                               '5.6% v 16.0%. Retain 3%.',
                                    'decision': 'agree',
                                    'grade': 'Randomised trial',
                                    'proposed': None,
                                    'source': 'Catto et al (iROC RCT, 9 UK centres), JAMA 2022;327:2092-103 '
                                              '(doi 10.1001/jama.2022.7393): overall complications similar '
                                              '(63.4% v 67.9%), but thromboembolic 1.9% v 8.3% and wound '
                                              '5.6% v 16.0%. Retain 3%.',
                                    'status': 'Sourced',
                                    'v07': 0.03,
                                    'value': 0.03},
 'cystectomy.conv_reduction_lap': {'comment': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                   'decision': 'needs evidence',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                   'status': 'Needs evidence',
                                   'v07': 0.03,
                                   'value': 0.03},
 'cystectomy.extra_minutes_lap': {'comment': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                  'decision': 'needs evidence',
                                  'grade': 'None',
                                  'proposed': None,
                                  'source': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                  'status': 'Needs evidence',
                                  'v07': 20.0,
                                  'value': 20.0},
 'cystectomy.extra_minutes_open': {'comment': 'Robotic cystectomy is longer than open in RCTs; iROC '
                                              'operating-time estimate not extracted. 60 may be low.',
                                   'decision': 'needs evidence',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'Robotic cystectomy is longer than open in RCTs; iROC '
                                             'operating-time estimate not extracted. 60 may be low.',
                                   'status': 'Needs evidence',
                                   'v07': 60.0,
                                   'value': 60.0},
 'cystectomy.los_reduction_lap': {'comment': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                  'decision': 'needs evidence',
                                  'grade': 'None',
                                  'proposed': None,
                                  'source': 'No robotic v laparoscopic cystectomy evidence reviewed.',
                                  'status': 'Needs evidence',
                                  'v07': 0.5,
                                  'value': 0.5},
 'cystectomy.los_reduction_open': {'comment': 'Catto et al (iROC RCT, 9 UK centres), JAMA 2022;327:2092-103 '
                                              '(doi 10.1001/jama.2022.7393): median stay 7 v 8 days; days '
                                              'alive and out of hospital at 90 days 82 v 80. Evidence does '
                                              'not support 2 days; the remaining benefit is through '
                                              'readmissions (see readm row).',
                                   'decision': 'change to',
                                   'grade': 'Randomised trial',
                                   'proposed': 1.0,
                                   'source': 'Catto et al (iROC RCT, 9 UK centres), JAMA 2022;327:2092-103 '
                                             '(doi 10.1001/jama.2022.7393): median stay 7 v 8 days; days '
                                             'alive and out of hospital at 90 days 82 v 80. Evidence does '
                                             'not support 2 days; the remaining benefit is through '
                                             'readmissions (see readm row).',
                                   'status': 'Sourced',
                                   'v07': 2.0,
                                   'value': 1.0},
 'cystectomy.p_open': {'comment': 'Laparoscopic cystectomy is uncommon in England, so the open share is '
                                  'probably above 80%; national data needed.',
                       'decision': 'needs evidence',
                       'grade': 'None',
                       'proposed': None,
                       'source': 'Laparoscopic cystectomy is uncommon in England, so the open share is '
                                 'probably above 80%; national data needed.',
                       'status': 'Needs evidence',
                       'v07': 0.8,
                       'value': 0.8},
 'cystectomy.readm_reduction_lap': {'comment': 'No evidence. Retain zero.',
                                    'decision': 'agree',
                                    'grade': 'None',
                                    'proposed': None,
                                    'source': 'No evidence. Retain zero.',
                                    'status': 'Clinical lead input',
                                    'v07': 0.0,
                                    'value': 0.0},
 'cystectomy.readm_reduction_open': {'comment': 'Catto et al (iROC RCT, 9 UK centres), JAMA '
                                                '2022;327:2092-103 (doi 10.1001/jama.2022.7393): readmission '
                                                'about 22% v 32% (21.8% v 32.2% as presented, EAU 2022), '
                                                'measured over 90 days. 7 points assumes about two-thirds '
                                                'fall within 30 days (assumption, unsourced).',
                                     'decision': 'change to',
                                     'grade': 'Randomised trial',
                                     'proposed': 0.07,
                                     'source': 'Catto et al (iROC RCT, 9 UK centres), JAMA 2022;327:2092-103 '
                                               '(doi 10.1001/jama.2022.7393): readmission about 22% v 32% '
                                               '(21.8% v 32.2% as presented, EAU 2022), measured over 90 '
                                               'days. 7 points assumes about two-thirds fall within 30 days '
                                               '(assumption, unsourced).',
                                     'status': 'Sourced',
                                     'v07': 0.0,
                                     'value': 0.07},
 'cystectomy.reop_reduction_lap': {'comment': 'No evidence. Retain zero.',
                                   'decision': 'agree',
                                   'grade': 'None',
                                   'proposed': None,
                                   'source': 'No evidence. Retain zero.',
                                   'status': 'Clinical lead input',
                                   'v07': 0.0,
                                   'value': 0.0},
 'cystectomy.reop_reduction_open': {'comment': 'Not extracted from iROC; retain placeholder.',
                                    'decision': 'needs evidence',
                                    'grade': 'None',
                                    'proposed': None,
                                    'source': 'Not extracted from iROC; retain placeholder.',
                                    'status': 'Needs evidence',
                                    'v07': 0.01,
                                    'value': 0.01},
 'gyn_oncology.comp_reduction_lap': {'comment': 'Narducci et al (ROBOGYN-1004 RCT), Gynecol Oncol '
                                                '2020;158:382-89: no difference in severe perioperative '
                                                'morbidity v laparoscopy.',
                                     'decision': 'change to',
                                     'grade': 'Randomised trial',
                                     'proposed': 0.0,
                                     'source': 'Narducci et al (ROBOGYN-1004 RCT), Gynecol Oncol '
                                               '2020;158:382-89: no difference in severe perioperative '
                                               'morbidity v laparoscopy.',
                                     'status': 'Sourced',
                                     'v07': 0.005,
                                     'value': 0.0},
 'gyn_oncology.comp_reduction_open': {'comment': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                                 'endometrial cancer; doi 10.1007/s11701-026-03625-w): '
                                                 'RASHEC 11 v 16 complications of 48 per arm; Lundin 2 v 5 '
                                                 'of 25; fewer minor and major Clavien-Dindo events. 4 '
                                                 'points is moderate.',
                                      'decision': 'change to',
                                      'grade': 'Randomised trial',
                                      'proposed': 0.04,
                                      'source': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                                'endometrial cancer; doi 10.1007/s11701-026-03625-w): RASHEC '
                                                '11 v 16 complications of 48 per arm; Lundin 2 v 5 of 25; '
                                                'fewer minor and major Clavien-Dindo events. 4 points is '
                                                'moderate.',
                                      'status': 'Sourced',
                                      'v07': 0.03,
                                      'value': 0.04},
 'gyn_oncology.conv_reduction_lap': {'comment': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                                'endometrial cancer; doi 10.1007/s11701-026-03625-w): '
                                                'conversion 0.7% v 8.4% (OR 0.17; 3 RCTs, 285 patients). '
                                                'Cusimano et al, Am J Obstet Gynecol 2019;221:410-28 (PMID '
                                                '31082383) shows smaller gaps (1-3 points) in obese women. 4 '
                                                'points is moderate.',
                                     'decision': 'change to',
                                     'grade': 'Randomised trial',
                                     'proposed': 0.04,
                                     'source': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                               'endometrial cancer; doi 10.1007/s11701-026-03625-w): '
                                               'conversion 0.7% v 8.4% (OR 0.17; 3 RCTs, 285 patients). '
                                               'Cusimano et al, Am J Obstet Gynecol 2019;221:410-28 (PMID '
                                               '31082383) shows smaller gaps (1-3 points) in obese women. 4 '
                                               'points is moderate.',
                                     'status': 'Sourced',
                                     'v07': 0.03,
                                     'value': 0.04},
 'gyn_oncology.extra_minutes_lap': {'comment': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                               'endometrial cancer; doi 10.1007/s11701-026-03625-w): RCTs '
                                               'inconsistent (theatre time -31 to +71 min). Retain 20.',
                                    'decision': 'agree',
                                    'grade': 'Randomised trial',
                                    'proposed': None,
                                    'source': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                              'endometrial cancer; doi 10.1007/s11701-026-03625-w): RCTs '
                                              'inconsistent (theatre time -31 to +71 min). Retain 20.',
                                    'status': 'Sourced',
                                    'v07': 20.0,
                                    'value': 20.0},
 'gyn_oncology.extra_minutes_open': {'comment': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                                'endometrial cancer; doi 10.1007/s11701-026-03625-w): robot '
                                                'v laparotomy operative time 233 v 187 min (RASHEC); theatre '
                                                'time 176 v 145 min (Lundin). 30 min used.',
                                     'decision': 'change to',
                                     'grade': 'Randomised trial',
                                     'proposed': 30.0,
                                     'source': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                               'endometrial cancer; doi 10.1007/s11701-026-03625-w): robot v '
                                               'laparotomy operative time 233 v 187 min (RASHEC); theatre '
                                               'time 176 v 145 min (Lundin). 30 min used.',
                                     'status': 'Sourced',
                                     'v07': 20.0,
                                     'value': 30.0},
 'gyn_oncology.los_reduction_lap': {'comment': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                               'endometrial cancer; doi 10.1007/s11701-026-03625-w): no '
                                               'clear stay difference v laparoscopy. Retain 0.2.',
                                    'decision': 'agree',
                                    'grade': 'Randomised trial',
                                    'proposed': None,
                                    'source': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                              'endometrial cancer; doi 10.1007/s11701-026-03625-w): no clear '
                                              'stay difference v laparoscopy. Retain 0.2.',
                                    'status': 'Sourced',
                                    'v07': 0.2,
                                    'value': 0.2},
 'gyn_oncology.los_reduction_open': {'comment': 'De Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                                'endometrial cancer; doi 10.1007/s11701-026-03625-w): robot '
                                                'v laparotomy stay 2 v 5 days (Salehi, RASHEC RCT) and 2 v 2 '
                                                'days (Lundin RCT). 2.0 is moderate.',
                                     'decision': 'change to',
                                     'grade': 'Randomised trial',
                                     'proposed': 2.0,
                                     'source': 'Clinical lead kept the v0.7 value (1.5); the literature '
                                               'review proposed 2, but the evidence is not yet considered '
                                               'reliable enough for bed-days or the open share. Review: De '
                                               'Angelis et al, J Robot Surg 2026;20:659 (RCT review, '
                                               'endometrial cancer; doi 10.1007/s11701-026-03625-w): robot v '
                                               'laparotomy stay 2 v 5 days (Salehi, RASHEC RCT) and 2 v 2 '
                                               'days (Lundin RCT). 2.0 is moderate.',
                                     'status': 'Clinical lead input',
                                     'v07': 1.5,
                                     'value': 1.5},
 'gyn_oncology.p_open': {'comment': 'Clinical lead opinion (compared mainly with open). Safety caveat: '
                                    'Ramirez et al (LACC), NEJM 2018;379:1895-904 (doi '
                                    '10.1056/NEJMoa1806395) found worse survival after minimally invasive '
                                    'radical hysterectomy for early cervical cancer, so benefits here should '
                                    'apply to endometrial cancer only.',
                         'decision': 'change to',
                         'grade': 'Clinical lead opinion',
                         'proposed': 0.6,
                         'source': 'Clinical lead kept the v0.7 value (50%); the literature review proposed '
                                   '0.6, but the evidence is not yet considered reliable enough for bed-days '
                                   'or the open share. Review: Clinical lead opinion (compared mainly with '
                                   'open). Safety caveat: Ramirez et al (LACC), NEJM 2018;379:1895-904 (doi '
                                   '10.1056/NEJMoa1806395) found worse survival after minimally invasive '
                                   'radical hysterectomy for early cervical cancer, so benefits here should '
                                   'apply to endometrial cancer only.',
                         'status': 'Clinical lead input',
                         'v07': 0.5,
                         'value': 0.5},
 'gyn_oncology.readm_reduction_lap': {'comment': 'No evidence of a difference. Retain zero.',
                                      'decision': 'agree',
                                      'grade': 'None',
                                      'proposed': None,
                                      'source': 'No evidence of a difference. Retain zero.',
                                      'status': 'Clinical lead input',
                                      'v07': 0.0,
                                      'value': 0.0},
 'gyn_oncology.readm_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                                  'review; value retained as placeholder.',
                                       'decision': 'needs evidence',
                                       'grade': 'None',
                                       'proposed': None,
                                       'source': 'No robotic v open comparative evidence identified in this '
                                                 'review; value retained as placeholder.',
                                       'status': 'Needs evidence',
                                       'v07': 0.005,
                                       'value': 0.005},
 'gyn_oncology.reop_reduction_lap': {'comment': 'No evidence of a difference. Retain zero.',
                                     'decision': 'agree',
                                     'grade': 'None',
                                     'proposed': None,
                                     'source': 'No evidence of a difference. Retain zero.',
                                     'status': 'Clinical lead input',
                                     'v07': 0.0,
                                     'value': 0.0},
 'gyn_oncology.reop_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                                 'review; value retained as placeholder.',
                                      'decision': 'needs evidence',
                                      'grade': 'None',
                                      'proposed': None,
                                      'source': 'No robotic v open comparative evidence identified in this '
                                                'review; value retained as placeholder.',
                                      'status': 'Needs evidence',
                                      'v07': 0.005,
                                      'value': 0.005},
 'inguinal.comp_reduction_lap': {'comment': 'Brucchi et al, Hernia 2025 (3 RCTs, 300 patients): no '
                                            'difference in complications. Retain zero.',
                                 'decision': 'agree',
                                 'grade': 'None',
                                 'proposed': None,
                                 'source': 'Brucchi et al, Hernia 2025 (3 RCTs, 300 patients): no difference '
                                           'in complications. Retain zero.',
                                 'status': 'Sourced',
                                 'v07': 0.0,
                                 'value': 0.0},
 'inguinal.comp_reduction_open': {'comment': 'Clinical lead opinion (no 30-day difference); no robotic v '
                                             'open RCT identified.',
                                  'decision': 'agree',
                                  'grade': 'Randomised trial',
                                  'proposed': None,
                                  'source': 'Clinical lead opinion (no 30-day difference); no robotic v open '
                                            'RCT identified.',
                                  'status': 'Sourced',
                                  'v07': 0.0,
                                  'value': 0.0},
 'inguinal.conv_reduction_lap': {'comment': 'RIVAL and Brucchi et al, Hernia 2025 (doi '
                                            '10.1007/s10029-025-03550-1): no difference. Retain zero.',
                                 'decision': 'agree',
                                 'grade': 'None',
                                 'proposed': None,
                                 'source': 'RIVAL and Brucchi et al, Hernia 2025 (doi '
                                           '10.1007/s10029-025-03550-1): no difference. Retain zero.',
                                 'status': 'Sourced',
                                 'v07': 0.0,
                                 'value': 0.0},
 'inguinal.extra_minutes_lap': {'comment': 'Brucchi et al, Hernia 2025 (doi 10.1007/s10029-025-03550-1): MD '
                                           '+17.6 min across 3 RCTs (not significant); RIVAL: 75.5 v 40.5 '
                                           'min. 18 min used.',
                                'decision': 'change to',
                                'grade': 'None',
                                'proposed': 18.0,
                                'source': 'Brucchi et al, Hernia 2025 (doi 10.1007/s10029-025-03550-1): MD '
                                          '+17.6 min across 3 RCTs (not significant); RIVAL: 75.5 v 40.5 '
                                          'min. 18 min used.',
                                'status': 'Sourced',
                                'v07': 0.0,
                                'value': 18.0},
 'inguinal.extra_minutes_open': {'comment': 'Robotic repair is likely longer than open mesh repair but no '
                                            'comparative estimate was found; zero probably understates '
                                            'theatre cost.',
                                 'decision': 'needs evidence',
                                 'grade': 'None',
                                 'proposed': None,
                                 'source': 'Robotic repair is likely longer than open mesh repair but no '
                                           'comparative estimate was found; zero probably understates '
                                           'theatre cost.',
                                 'status': 'Needs evidence',
                                 'v07': 0.0,
                                 'value': 0.0},
 'inguinal.los_reduction_lap': {'comment': 'Prabhu et al (RIVAL RCT), JAMA Surg 2020;155:380-87 (doi '
                                           '10.1001/jamasurg.2020.0034; PMID 32186683): no 30-day '
                                           'difference. Retain zero.',
                                'decision': 'agree',
                                'grade': 'Randomised trial',
                                'proposed': None,
                                'source': 'Prabhu et al (RIVAL RCT), JAMA Surg 2020;155:380-87 (doi '
                                          '10.1001/jamasurg.2020.0034; PMID 32186683): no 30-day difference. '
                                          'Retain zero.',
                                'status': 'Sourced',
                                'v07': 0.0,
                                'value': 0.0},
 'inguinal.los_reduction_open': {'comment': 'Clinical lead opinion (no 30-day difference); no robotic v open '
                                            'RCT identified. Both usually day case.',
                                 'decision': 'agree',
                                 'grade': 'Randomised trial',
                                 'proposed': None,
                                 'source': 'Clinical lead opinion (no 30-day difference); no robotic v open '
                                           'RCT identified. Both usually day case.',
                                 'status': 'Sourced',
                                 'v07': 0.0,
                                 'value': 0.0},
 'inguinal.p_open': {'comment': 'No source for the open share of complex (recurrent or bilateral) inguinal '
                                'repair. Retain 30% pending data.',
                     'decision': 'needs evidence',
                     'grade': 'None',
                     'proposed': None,
                     'source': 'No source for the open share of complex (recurrent or bilateral) inguinal '
                               'repair. Retain 30% pending data.',
                     'status': 'Needs evidence',
                     'v07': 0.3,
                     'value': 0.3},
 'inguinal.readm_reduction_lap': {'comment': 'No difference in RCTs (RIVAL; Brucchi 2025). Retain zero.',
                                  'decision': 'agree',
                                  'grade': 'None',
                                  'proposed': None,
                                  'source': 'No difference in RCTs (RIVAL; Brucchi 2025). Retain zero.',
                                  'status': 'Sourced',
                                  'v07': 0.0,
                                  'value': 0.0},
 'inguinal.readm_reduction_open': {'comment': 'Clinical lead opinion (no 30-day difference).',
                                   'decision': 'agree',
                                   'grade': 'Clinical lead opinion',
                                   'proposed': None,
                                   'source': 'Clinical lead opinion (no 30-day difference).',
                                   'status': 'Clinical lead input',
                                   'v07': 0.0,
                                   'value': 0.0},
 'inguinal.reop_reduction_lap': {'comment': 'No difference in RCTs (RIVAL; Brucchi 2025). Retain zero.',
                                 'decision': 'agree',
                                 'grade': 'None',
                                 'proposed': None,
                                 'source': 'No difference in RCTs (RIVAL; Brucchi 2025). Retain zero.',
                                 'status': 'Sourced',
                                 'v07': 0.0,
                                 'value': 0.0},
 'inguinal.reop_reduction_open': {'comment': 'Clinical lead opinion (no 30-day difference).',
                                  'decision': 'agree',
                                  'grade': 'Clinical lead opinion',
                                  'proposed': None,
                                  'source': 'Clinical lead opinion (no 30-day difference).',
                                  'status': 'Clinical lead input',
                                  'v07': 0.0,
                                  'value': 0.0},
 'prostatectomy.comp_reduction_open': {'comment': 'Ilic et al, Cochrane CD009625.pub2, 2017 (doi '
                                                  '10.1002/14651858.CD009625.pub2): overall complications RR '
                                                  '0.41 (0.16-1.04), serious RR 0.16 (0.02-1.32), low '
                                                  'certainty; Yaxley et al, Lancet 2016;388:1057-66 (doi '
                                                  '10.1016/S0140-6736(16)30592-X): 9% v 4%. Retain 2%.',
                                       'decision': 'agree',
                                       'grade': 'Cochrane systematic review',
                                       'proposed': None,
                                       'source': 'Ilic et al, Cochrane CD009625.pub2, 2017 (doi '
                                                 '10.1002/14651858.CD009625.pub2): overall complications RR '
                                                 '0.41 (0.16-1.04), serious RR 0.16 (0.02-1.32), low '
                                                 'certainty; Yaxley et al, Lancet 2016;388:1057-66 (doi '
                                                 '10.1016/S0140-6736(16)30592-X): 9% v 4%. Retain 2%.',
                                       'status': 'Sourced',
                                       'v07': 0.02,
                                       'value': 0.02},
 'prostatectomy.extra_minutes_open': {'comment': 'RCTs conflict: Yaxley 2016 found shorter robotic operating '
                                                 'time (very experienced robotic surgeon); a later '
                                                 'single-centre RCT (Nahas et al, as summarised by Cooley et '
                                                 'al, Transl Androl Urol) reported 212 v 120 min. Zero may '
                                                 'understate cost.',
                                      'decision': 'needs evidence',
                                      'grade': 'Randomised trial',
                                      'proposed': None,
                                      'source': 'RCTs conflict: Yaxley 2016 found shorter robotic operating '
                                                'time (very experienced robotic surgeon); a later '
                                                'single-centre RCT (Nahas et al, as summarised by Cooley et '
                                                'al, Transl Androl Urol) reported 212 v 120 min. Zero may '
                                                'understate cost.',
                                      'status': 'Needs evidence',
                                      'v07': 0.0,
                                      'value': 0.0},
 'prostatectomy.los_reduction_open': {'comment': 'Ilic et al, Cochrane CD009625.pub2, 2017 (doi '
                                                 '10.1002/14651858.CD009625.pub2): stay MD -1.72 days (-2.19 '
                                                 'to -1.25; moderate certainty; trial-era robotic stay 1-1.5 '
                                                 'days). Abaza et al, J Urol 2019;202:959-63 (PMID '
                                                 '31112102): 49% same-day discharge, mean 0.51 days (single '
                                                 'surgeon); national uptake is lower (France 1.9% in 2020, '
                                                 'Eur Urol Open Sci 2022;36:23-25). 0.75-day uplift above '
                                                 '1.72 is clinical lead opinion.',
                                      'decision': 'change to',
                                      'grade': 'Cochrane systematic review',
                                      'proposed': 2.5,
                                      'source': 'Clinical lead kept the v0.7 value (2); the literature '
                                                'review proposed 2.5, but the evidence is not yet considered '
                                                'reliable enough for bed-days or the open share. Review: '
                                                'Ilic et al, Cochrane CD009625.pub2, 2017 (doi '
                                                '10.1002/14651858.CD009625.pub2): stay MD -1.72 days (-2.19 '
                                                'to -1.25; moderate certainty; trial-era robotic stay 1-1.5 '
                                                'days). Abaza et al, J Urol 2019;202:959-63 (PMID 31112102): '
                                                '49% same-day discharge, mean 0.51 days (single surgeon); '
                                                'national uptake is lower (France 1.9% in 2020, Eur Urol '
                                                'Open Sci 2022;36:23-25). 0.75-day uplift above 1.72 is '
                                                'clinical lead opinion.',
                                      'status': 'Clinical lead input',
                                      'v07': 2.0,
                                      'value': 2.0},
 'prostatectomy.p_open': {'comment': 'Fixed project decision: open is the comparator.',
                          'decision': 'agree',
                          'grade': 'None',
                          'proposed': None,
                          'source': 'Fixed project decision: open is the comparator.',
                          'status': 'Clinical lead input',
                          'v07': 1.0,
                          'value': 1.0},
 'prostatectomy.readm_reduction_open': {'comment': 'Maynou et al, Health Serv Res 2021;56(S3):1441-61 '
                                                   '(England HES 2005-17): fewer 30-day readmissions after '
                                                   'minimally invasive than open prostatectomy (size not '
                                                   'extracted). Retain 0.5%.',
                                        'decision': 'agree',
                                        'grade': 'Observational',
                                        'proposed': None,
                                        'source': 'Maynou et al, Health Serv Res 2021;56(S3):1441-61 '
                                                  '(England HES 2005-17): fewer 30-day readmissions after '
                                                  'minimally invasive than open prostatectomy (size not '
                                                  'extracted). Retain 0.5%.',
                                        'status': 'Sourced',
                                        'v07': 0.005,
                                        'value': 0.005},
 'prostatectomy.reop_reduction_open': {'comment': 'No reoperation estimate identified.',
                                       'decision': 'needs evidence',
                                       'grade': 'None',
                                       'proposed': None,
                                       'source': 'No reoperation estimate identified.',
                                       'status': 'Needs evidence',
                                       'v07': 0.005,
                                       'value': 0.005},
 'rectal.comp_reduction_lap': {'comment': 'Feng et al (REAL RCT), Lancet Gastroenterol Hepatol '
                                          '2022;7:991-1004 (doi 10.1016/S2468-1253(22)00248-5; PMID '
                                          '36087608): Clavien-Dindo III+ difference -1.5 points (not '
                                          'significant); grade II+ 16.2% v 23.1% (-6.9 points). 1.0 point '
                                          'for major complications is moderate.',
                               'decision': 'change to',
                               'grade': 'Randomised trial',
                               'proposed': 0.01,
                               'source': 'Feng et al (REAL RCT), Lancet Gastroenterol Hepatol '
                                         '2022;7:991-1004 (doi 10.1016/S2468-1253(22)00248-5; PMID '
                                         '36087608): Clavien-Dindo III+ difference -1.5 points (not '
                                         'significant); grade II+ 16.2% v 23.1% (-6.9 points). 1.0 point for '
                                         'major complications is moderate.',
                               'status': 'Sourced',
                               'v07': 0.005,
                               'value': 0.01},
 'rectal.comp_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                           'review; value retained as placeholder.',
                                'decision': 'needs evidence',
                                'grade': 'None',
                                'proposed': None,
                                'source': 'No robotic v open comparative evidence identified in this review; '
                                          'value retained as placeholder.',
                                'status': 'Needs evidence',
                                'v07': 0.04,
                                'value': 0.04},
 'rectal.conv_reduction_lap': {'comment': 'Feng et al (REAL RCT), Lancet Gastroenterol Hepatol '
                                          '2022;7:991-1004 (doi 10.1016/S2468-1253(22)00248-5; PMID '
                                          '36087608): conversion 1.7% v 3.9% (expert centres, low baseline); '
                                          'Zou et al, BMC Surg 2025;25:86 (RCT meta-analysis; doi '
                                          '10.1186/s12893-025-02805-z): OR 0.42 (0.28-0.63). On an assumed '
                                          'NHS laparoscopic conversion of 9-10% (assumption) OR 0.42 implies '
                                          'about 5 points. Retain 5%.',
                               'decision': 'agree',
                               'grade': 'Meta-analysis of randomised trials',
                               'proposed': None,
                               'source': 'Feng et al (REAL RCT), Lancet Gastroenterol Hepatol '
                                         '2022;7:991-1004 (doi 10.1016/S2468-1253(22)00248-5; PMID '
                                         '36087608): conversion 1.7% v 3.9% (expert centres, low baseline); '
                                         'Zou et al, BMC Surg 2025;25:86 (RCT meta-analysis; doi '
                                         '10.1186/s12893-025-02805-z): OR 0.42 (0.28-0.63). On an assumed '
                                         'NHS laparoscopic conversion of 9-10% (assumption) OR 0.42 implies '
                                         'about 5 points. Retain 5%.',
                               'status': 'Sourced',
                               'v07': 0.05,
                               'value': 0.05},
 'rectal.extra_minutes_lap': {'comment': 'Rectal-specific RCT operating-time estimate not extracted. Colon '
                                         'meta-analysis shows +43 min (Cuk 2022), so 20 may be low.',
                              'decision': 'needs evidence',
                              'grade': 'Meta-analysis of randomised trials',
                              'proposed': None,
                              'source': 'Rectal-specific RCT operating-time estimate not extracted. Colon '
                                        'meta-analysis shows +43 min (Cuk 2022), so 20 may be low.',
                              'status': 'Needs evidence',
                              'v07': 20.0,
                              'value': 20.0},
 'rectal.extra_minutes_open': {'comment': 'No robotic v open comparative evidence identified in this review; '
                                          'value retained as placeholder.',
                               'decision': 'needs evidence',
                               'grade': 'None',
                               'proposed': None,
                               'source': 'No robotic v open comparative evidence identified in this review; '
                                         'value retained as placeholder.',
                               'status': 'Needs evidence',
                               'v07': 30.0,
                               'value': 30.0},
 'rectal.los_reduction_lap': {'comment': 'Feng et al (REAL RCT), Lancet Gastroenterol Hepatol '
                                         '2022;7:991-1004 (doi 10.1016/S2468-1253(22)00248-5; PMID '
                                         '36087608): median stay 7 v 8 days (difference -1.0; long Chinese '
                                         'stays, may shrink under ERAS); Zou et al, BMC Surg 2025;25:86 (RCT '
                                         'meta-analysis; doi 10.1186/s12893-025-02805-z) found no pooled '
                                         'stay difference. 0.75 is a moderate midpoint.',
                              'decision': 'change to',
                              'grade': 'Meta-analysis of randomised trials',
                              'proposed': 0.75,
                              'source': 'Clinical lead kept the v0.7 value (0.5); the literature review '
                                        'proposed 0.75, but the evidence is not yet considered reliable '
                                        'enough for bed-days or the open share. Review: Feng et al (REAL '
                                        'RCT), Lancet Gastroenterol Hepatol 2022;7:991-1004 (doi '
                                        '10.1016/S2468-1253(22)00248-5; PMID 36087608): median stay 7 v 8 '
                                        'days (difference -1.0; long Chinese stays, may shrink under ERAS); '
                                        'Zou et al, BMC Surg 2025;25:86 (RCT meta-analysis; doi '
                                        '10.1186/s12893-025-02805-z) found no pooled stay difference. 0.75 '
                                        'is a moderate midpoint.',
                              'status': 'Clinical lead input',
                              'v07': 0.5,
                              'value': 0.5},
 'rectal.los_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this review; '
                                          'value retained as placeholder.',
                               'decision': 'needs evidence',
                               'grade': 'None',
                               'proposed': None,
                               'source': 'No robotic v open comparative evidence identified in this review; '
                                         'value retained as placeholder.',
                               'status': 'Needs evidence',
                               'v07': 2.0,
                               'value': 2.0},
 'rectal.p_open': {'comment': 'As colectomy: NBOCA figure is population context only. Retain 10% pending '
                              'local data.',
                   'decision': 'needs evidence',
                   'grade': 'None',
                   'proposed': None,
                   'source': 'As colectomy: NBOCA figure is population context only. Retain 10% pending '
                             'local data.',
                   'status': 'Needs evidence',
                   'v07': 0.1,
                   'value': 0.1},
 'rectal.readm_reduction_lap': {'comment': 'No evidence of a readmission difference identified. Retain zero.',
                                'decision': 'agree',
                                'grade': 'None',
                                'proposed': None,
                                'source': 'No evidence of a readmission difference identified. Retain zero.',
                                'status': 'Clinical lead input',
                                'v07': 0.0,
                                'value': 0.0},
 'rectal.readm_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                            'review; value retained as placeholder.',
                                 'decision': 'needs evidence',
                                 'grade': 'None',
                                 'proposed': None,
                                 'source': 'No robotic v open comparative evidence identified in this '
                                           'review; value retained as placeholder.',
                                 'status': 'Needs evidence',
                                 'v07': 0.01,
                                 'value': 0.01},
 'rectal.reop_reduction_lap': {'comment': 'Zou et al, BMC Surg 2025;25:86 (RCT meta-analysis; doi '
                                          '10.1186/s12893-025-02805-z): reoperation OR 0.45. On an assumed '
                                          'laparoscopic reoperation risk of about 2% (assumption) this gives '
                                          'about 1 point.',
                               'decision': 'change to',
                               'grade': 'Meta-analysis of randomised trials',
                               'proposed': 0.01,
                               'source': 'Zou et al, BMC Surg 2025;25:86 (RCT meta-analysis; doi '
                                         '10.1186/s12893-025-02805-z): reoperation OR 0.45. On an assumed '
                                         'laparoscopic reoperation risk of about 2% (assumption) this gives '
                                         'about 1 point.',
                               'status': 'Sourced',
                               'v07': 0.005,
                               'value': 0.01},
 'rectal.reop_reduction_open': {'comment': 'No robotic v open comparative evidence identified in this '
                                           'review; value retained as placeholder.',
                                'decision': 'needs evidence',
                                'grade': 'None',
                                'proposed': None,
                                'source': 'No robotic v open comparative evidence identified in this review; '
                                          'value retained as placeholder.',
                                'status': 'Needs evidence',
                                'v07': 0.02,
                                'value': 0.02}}
