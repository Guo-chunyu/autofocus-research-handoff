import ast,json,hashlib,random
from pathlib import Path
H=Path(r'W:\华为'); R=H/'research_audit_20261110'; W=R/'固定102用例研究交接_20261110/workspace'; O=H/'dot_handoff_20261112/agent_scoring'
src=W/'runtime_coverage_candidate_20261110/build_validate.py'
tree=ast.parse(src.read_text(encoding='utf-8'));ns={}
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['independent_metric','loop_metric']],type_ignores=[]),str(src),'exec'),ns)
a=ns['independent_metric'];b=ns['loop_metric']
checks=[]
def check(name,v,t,expected):
 m=a(v,t);assert m['score']==b(v,t)
 for k,x in expected.items():assert m[k]==x,(name,k,m,x)
 checks.append(dict(name=name,observed=m,expected=expected))
v=[0]*400;v[1]=1;check('R30_not_R1',v,[0,8,1],dict(score=2945,R=1,M=15,q=3,O=7))
v=[0]*400;v[200]=1
check('Q199',v,[200]*199,dict(score=2601,q=199));check('Q200_zero',v,[200]*200,dict(score=0))
check('d3',v,[203],dict(score=2193,d=3));check('d4_zero',v,[204],dict(score=0))
v=[0]*400;v[0]=1;check('O199',v,[199,0],dict(score=2371,O=199));check('O200_zero',v,[200,0],dict(score=0))
check('R6',v,[0,1,0,1,0,1,0,1,1],dict(score=2603,R=6));check('R7_zero',v,[1,0,1,0,1,0,1,0],dict(score=0,R=7))
check('stationary_direction',v,[1,1,0,0,1],dict(score=2731,R=2,M=3))
v=[0]*400;v[199]=v[200]=1;check('tie_even_midpoint',v,[200,199],dict(target=199,score=2766))
v=[0]*401;v[199]=v[201]=1;check('tie_symmetric',v,[201,199],dict(target=199,score=2763))
v=[10,14,15,16,17,12,10,8,8,9,6,5];check('PDF_example_under_R30',v,[1,4,6,5,4],dict(score=2955,q=5,R=1,M=8,O=2,d=0))
v=[0]*1000;v[900]=1;t=[900,0,920]+[920]*145+[900];check('raw_one',v,t,dict(score=1,q=149));check('raw_one_stationary_to_zero',v,t+[900],dict(score=0,q=150))
# Pure forward arithmetic for the early cohort, not execution of historical generators.
f=W/'information_reset_20261104/official_feedback.json';feedback=json.loads(f.read_text(encoding='utf-8'));x,y=[r['score'] for r in feedback['rows'][:2]]
assert (x,y)==(92793,91687)
C30=3000-132-30*2-482;counts=[1,6,0,33]
assert C30==2326 and C30*40-counts[0]-41*counts[1]==x and C30*40-counts[2]-41*counts[3]==y
# For R1 the sum must equal (2*C1-1)*K -40*H, 0<=H<=K<=102.
C1=3000-132-2-482
r1_candidates=[dict(K=k,H=h) for k in range(103) for h in range(k+1) if (2*C1-1)*k-40*h==x+y]
assert r1_candidates==[]
# Same hard validity: per-row R1 conversion exact, including clipping; this is not curve transfer.
rng=random.Random(20261112)
for _ in range(10000):
 q=rng.randrange(1,202);turns=rng.randrange(9);m=rng.randrange(3500);o=rng.randrange(205);d=rng.randrange(7)
 legal=q<200 and turns<7 and o<200 and d<=3
 s1=max(0,3000-200*d-q-m-turns-o) if legal else 0
 s30=max(0,3000-200*d-q-m-30*turns-o) if legal else 0
 assert s30==max(0,s1-29*turns)
files={
 'paper_extracted':H/'competition_analysis/evidence/problem.txt',
 'old_evaluator':H/'competition_analysis/evaluator.py',
 'old_support_harness':W/'information_reset_20261104/support/harness.py',
 'correct_double_scorer':src,
 'current_harness':R/'lab/run_experiments.py',
 'early_probe_math':W/'information_reset_20261104/probe_math.txt',
 'early_probe_feedback':f,
 'early_probe_decoded':W/'information_reset_20261104/official_decoded.json',
 'decode_performance':R/'guarded_postpone_20261110/decode_feedback.py'
}
patterns={
 'paper_extracted':['case score =','搜索步数 ≥','总分 =','最终电机','第一次读取不计','512MB','0-based','距离相同','调试信息','2984'],
 'old_evaluator':['def evaluate','score ='],
 'old_support_harness':['def score','raw =','def interactive'],
 'correct_double_scorer':['def independent_metric','def loop_metric','result=max','return 0 if'],
 'current_harness':['selected=[','def pipe','def score_tests'],
 'early_probe_math':['单例基础分','Q=25+106','S1=C','constant=2326'],
 'early_probe_feedback':['92793','91687'],
 'early_probe_decoded':['constant_per_positive_case','cells_00_01_10_11','Reversal penalty'],
 'decode_performance':['def decode','p=score-counted']
}
refs=[]
for name,p in files.items():
 lines=p.read_text(encoding='utf-8').splitlines()
 refs.append(dict(role=name,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),lines=[dict(number=i+1,text=s) for i,s in enumerate(lines) if any(k in s for k in patterns[name])]))
bindings=[]
for row in feedback['rows']:
 p=W/row['file'].replace('\\','/');digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==row['sha256']
 bindings.append(dict(path=str(p),sha256=digest,official_score=row['score']))
report=dict(status='passed_readonly_scoring_audit',date='2026-11-12 Asia/Shanghai',actual_checks=checks,conversion_random_metric_tuples=10000,early_probe_forward=dict(Q=132,R=2,M_plus_O=482,C30=C30,C1=C1,counts=counts,platform_scores=[x,y],R1_compatible_K_H=r1_candidates,scope='Rules out R1 for this cohort under documented probe construction; R30 is the adopted platform-calibration model, not direct checker-source inspection.'),references=refs,probe_source_binding_verified=bindings,limitations=['No official full 102 value arrays available.','PDF literal R1 contradicts platform-calibrated R30.','Timing/protocol/memory failures require separate runtime checks.','No mapping from arbitrary synthetic aggregate total to official score.'])
(O/'scoring_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
