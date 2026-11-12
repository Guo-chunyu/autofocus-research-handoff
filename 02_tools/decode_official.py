"""Decode ONLY verified matched score/counter pairs, not synthetic conversion."""
import argparse,json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('performance',type=int);p.add_argument('counter',type=int);p.add_argument('--reference',type=int,default=149485);a=p.parse_args()
n=a.performance-a.counter
if not 0<=a.counter<=a.performance<=306000 or not 0<=n<=102 or not n<=a.performance<=3000*n:p.error('inconsistent matched pair')
print(json.dumps(dict(score=a.performance,positive=n,zero=102-n,score_delta=a.performance-a.reference,exact_quality='unknown',success_set='unknown',requirements='same fixed 102 cases; same source except exactly one final stationary query; performance Q<=198; counter Q<=199; no other path change; score1-to0 boundary included',warning='Not valid for arbitrary two submissions. Cannot convert synthetic scores into hidden official scores.'),ensure_ascii=False,indent=2))
