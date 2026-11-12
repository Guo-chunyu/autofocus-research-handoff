"""R30 scoring of an actual trajectory, NOT a predictor of hidden official cases."""
import argparse,json
from pathlib import Path

def score_trace(values,trace):
    if not 400<=len(values)<=1000 or any(type(y)!=int or not 0<=y<=2147483647 for y in values):
        raise ValueError('require 400..1000 integer values in 0..INT_MAX')
    if not trace or any(type(x)!=int or not 0<=x<len(values) for x in trace):
        raise ValueError('require nonempty, integer, in-range actual query trajectory')
    target=min(range(len(values)),key=lambda x:(-values[x],abs(2*x-len(values)+1),x))
    travel=sum(abs(b-a) for a,b in zip([0]+trace,trace))
    signs=[(b>a)-(b<a) for a,b in zip([0]+trace,trace) if b!=a]
    turns=sum(a!=b for a,b in zip(signs,signs[1:]))
    q=len(trace);over=max(0,max(trace)-target);error=abs(trace[-1]-target)
    legal=q<200 and turns<7 and over<200 and error<=3
    raw=3000-200*error-q-travel-30*turns
    raw-=over
    score=max(0,raw) if legal else 0
    # Independently accumulate movement/turns, matching the frozen double scorer.
    pos=direction=R=M=far=0
    for x in trace:
        d=(x>pos)-(x<pos)
        if d and direction and d!=direction:R+=1
        if d:direction=d
        M+=abs(x-pos);pos=x;far=max(far,x)
    second=0 if q>=200 or R>=7 or abs(pos-target)>3 or max(0,far-target)>=200 else max(0,3000-200*abs(pos-target)-q-M-30*R-max(0,far-target))
    assert score==second and R==turns and M==travel
    return dict(score=score,q=q,R=turns,M=travel,O=over,d=error,target=target,last=trace[-1],raw_R30=raw,hard_legal=legal,
                legacy_R1_score=max(0,raw+29*turns) if legal else 0,
                scope='same supplied input and actual trajectory; not hidden-platform prediction')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',help='JSON with values and trace');p.add_argument('--out');a=p.parse_args()
    obj=json.loads(Path(a.input).read_text(encoding='utf-8-sig'));result=score_trace(obj['values'],obj['trace']);s=json.dumps(result,ensure_ascii=False,indent=2)
    if a.out:Path(a.out).write_text(s+'\n',encoding='utf-8')
    print(s)
