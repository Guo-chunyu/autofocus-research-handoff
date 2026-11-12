"""Read portable outputs; do not rerun the 6912 source cases or edit tools."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;PKG=HERE.parent/'package'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fields=['score','q','R','M','O','d','target','last']
actual=read(PKG/'06_verification/full12_batch/metrics.json');expected=read(PKG/'04_data/expected_12_6912.json')
assert len(actual)==len(expected)==6912
for i,(a,b) in enumerate(zip(actual,expected)):
    assert a['row']==i
    for k in fields:assert a[k]==b[k],(i,k,a[k],b[k])
full=read(PKG/'06_verification/full12_batch/traces.json');smoke=read(PKG/'04_data/smoke_7.json')['cases'];pipe=read(PKG/'06_verification/smoke_pipe/traces.json');pm=read(PKG/'06_verification/smoke_pipe/metrics.json')
assert len(smoke)==len(pipe)==len(pm)==7;links=[]
for j,(c,t,m) in enumerate(zip(smoke,pipe,pm)):
    i=c['original_row'];assert t==full[i]
    for k in fields:assert m[k]==actual[i][k],(j,i,k)
    log=read(PKG/f'06_verification/smoke_pipe/pipe_{j}.json')
    assert log['exit']==0 and not log['stderr'] and not log['extra'] and log['stdout'][-1]=='DONE\n'
    assert [int(x.strip()) for x in log['stdout'][:-1]]==t
    links.append(dict(smoke_row=j,original_row=i,queries=len(t),score=m['score']))
tool_hashes={s:sha(PKG/'02_tools'/s) for s in ['simulate.py','score_trace.py','history.py']}
# Exercise restore guards on tiny extra fixtures, never on the real package index.
fixture=HERE/'portable_history_fixture';fixture.mkdir(exist_ok=True)
obj=b'portable restore check\n';digest=hashlib.sha256(obj).hexdigest();objects=fixture/'05_history/objects';objects.mkdir(parents=True,exist_ok=True);(objects/digest).write_bytes(obj)
entries=[dict(path='one.txt',sha256=digest,bytes=len(obj)),dict(path='nested/two.txt',sha256=digest,bytes=len(obj))]
save(fixture/'05_history/history_index.json',dict(files=entries))
checks=[]
def run(args,tag):
    cmd=[sys.executable,str(PKG/'02_tools/history.py')]+args
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
    (HERE/(tag+'.stdout')).write_text(r.stdout,encoding='utf-8');(HERE/(tag+'.stderr')).write_text(r.stderr,encoding='utf-8')
    checks.append(dict(name=tag,command=cmd,exit=r.returncode));return r
r=run(['verify','--root',str(fixture)],'history_verify_fixture');assert r.returncode==0
out=HERE/'portable_restore_fixture';assert not out.exists()
r=run(['extract','--root',str(fixture),'--out',str(out)],'history_extract_fixture');assert r.returncode==0 and (out/'one.txt').read_bytes()==obj and (out/'nested/two.txt').read_bytes()==obj
before=sha(out/'one.txt')
r=run(['extract','--root',str(fixture),'--out',str(out)],'history_refuse_overwrite');assert r.returncode!=0 and sha(out/'one.txt')==before
entries[0]['path']='../escape_forbidden.txt';save(fixture/'05_history/history_index.json',dict(files=entries))
unsafe=HERE/'portable_unsafe_restore';assert not unsafe.exists() and not (HERE/'escape_forbidden.txt').exists()
r=run(['extract','--root',str(fixture),'--out',str(unsafe)],'history_refuse_traversal');assert r.returncode!=0 and not (HERE/'escape_forbidden.txt').exists()
save(fixture/'05_history/history_index.json',dict(files=[dict(path='one.txt',sha256=digest,bytes=len(obj)),dict(path='nested/two.txt',sha256=digest,bytes=len(obj))]))
assert tool_hashes=={s:sha(PKG/'02_tools'/s) for s in tool_hashes}
report=dict(status='passed_with_nonblocking_notes',full_cases=6912,fields_checked=fields,field_comparisons=6912*len(fields),total_score=sum(x['score'] for x in actual),positive=sum(x['score']>0 for x in actual),exact_positive=sum(x['score']>0 and x['d']==0 for x in actual),smoke_links=links,new_solver_runs=0,tool_files_unchanged=True,tool_sha256=tool_hashes,history_fixture_checks=checks,
    no_blocking_issue_found='R30 metrics match frozen expected results; smoke pipe matches batch; restore refuses nonempty destination and path traversal.',
    static_review_notes=[
      dict(severity='informational',tool='simulate.py',note='Batch adapter replaces I/O and requires supplied Search structure; other sources should use pipe. This restriction is explicit in docstring and runtime checks.'),
      dict(severity='informational',tool='score_trace.py',note='Per-case exact scoring only. scope and official_score_prediction=null correctly avoid claiming hidden102 prediction.'),
      dict(severity='low',tool='simulate.py',note='Negative --ids are accepted by Python indexing and recorded as negative row IDs. Default/full and supplied smoke usage unaffected; recommend explicit 0<=row<len(cases).'),
      dict(severity='low',tool='simulate.py',note='Early pipe failures before DONE raise before writing the pipe JSON. Successful current runs are fully logged; for future protocol debugging, consider finally-path capture of partial transcript.'),
      dict(severity='low',tool='history.py',note='verify validates byte-size only for first occurrence of a deduplicated digest; a corrupted repeated index entry with same SHA but wrong bytes field could be skipped. Extraction revalidates each entry. Real package index was not yet present during this review, so no assertion made about its duplicate-length consistency.'),
      dict(severity='informational',tool='score_trace.py',note='CLI --out explicitly allows replacing the named file; this is not a history extraction path. Use a new output name as documented workflow.')],
    checked_files=[dict(path=str(PKG/s),sha256=sha(PKG/s)) for s in ['06_verification/full12_batch/metrics.json','04_data/expected_12_6912.json','06_verification/full12_batch/traces.json','06_verification/smoke_pipe/traces.json','04_data/smoke_7.json']])
save(HERE/'portable_review.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ['static_review_notes','checked_files','history_fixture_checks']},ensure_ascii=False,indent=2))
