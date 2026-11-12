"""Compile C++17 and collect actual/simulated queries. Standard library only.
Batch mode is only for provided Search/readNumber/emitQuery/LOCAL_BATCH sources.
Generic other C++ submissions must use --mode pipe (actual flushed protocol).
"""
import argparse,hashlib,json,queue,shutil,subprocess,threading,time
from pathlib import Path
from score_trace import score_trace

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def command(argv,prefix,payload=None):
    r=subprocess.run(list(map(str,argv)),input=payload,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=300)
    prefix.with_suffix('.stdout').write_text(r.stdout,encoding='utf-8');prefix.with_suffix('.stderr').write_text(r.stderr,encoding='utf-8')
    save(prefix.with_suffix('.json'),dict(command=list(map(str,argv)),exit=r.returncode,input_sha256=hashlib.sha256(payload.encode()).hexdigest() if payload is not None else None))
    if r.returncode:raise RuntimeError('command failed; see '+str(prefix.with_suffix('.stderr')))
    return r

def pipe(exe,v,path):
    proc=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    lines=queue.Queue();output=[];answers=[str(len(v))+'\n'];trace=[]
    def reader():
        for line in proc.stdout:lines.put(line)
        lines.put(None)
    t=threading.Thread(target=reader,daemon=True);t.start();started=time.monotonic()
    try:
        proc.stdin.write(answers[0]);proc.stdin.flush()
        while True:
            line=lines.get(timeout=max(.01,20-(time.monotonic()-started)))
            if line is None:raise RuntimeError('missing DONE')
            output.append(line)
            if line=='DONE\n':break
            if not line.endswith('\n') or not line.strip().isdecimal():raise RuntimeError('unexpected stdout '+repr(line))
            x=int(line)
            if not 0<=x<len(v) or len(trace)>=1000:raise RuntimeError('illegal query / excessive output')
            trace.append(x);reply=str(v[x])+'\n';answers.append(reply);proc.stdin.write(reply);proc.stdin.flush()
        proc.stdin.close();proc.wait(timeout=3);t.join(timeout=1);extra=[]
        while not lines.empty():
            line=lines.get_nowait()
            if line is not None:extra.append(line)
        err=proc.stderr.read()
        save(path,dict(command=[str(exe)],stdin=answers,stdout=output,stderr=err,exit=proc.returncode,extra=extra))
        if proc.returncode or extra or err:raise RuntimeError('protocol/exit/stderr check failed')
        return trace
    except Exception as error:
        if proc.poll() is None:proc.kill();proc.wait()
        save(path,dict(command=[str(exe)],stdin=answers,stdout=output,stderr=proc.stderr.read(),exit=proc.returncode,failure=repr(error),complete=False))
        raise
    finally:
        if proc.poll() is None:proc.kill();proc.wait()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--cases',required=True);p.add_argument('--out',required=True)
    p.add_argument('--mode',choices=['batch','pipe'],default='pipe');p.add_argument('--compiler',default='g++');p.add_argument('--ids',help='zero-based rows, comma-separated');a=p.parse_args()
    src=Path(a.source).resolve();cp=Path(a.cases).resolve();out=Path(a.out).resolve()
    if out.exists() and any(out.iterdir()):p.error('out must be new/empty; never overwrite past experiment')
    out.mkdir(parents=True,exist_ok=True)
    obj=json.loads(cp.read_text(encoding='utf-8-sig'));cs=obj['cases'] if isinstance(obj,dict) else obj
    ids=list(map(int,a.ids.split(','))) if a.ids else list(range(len(cs)))
    if not ids or any(i<0 or i>=len(cs) for i in ids) or len(ids)!=len(set(ids)):p.error('ids must be distinct in-range nonnegative row indices')
    vals=[cs[i]['values'] for i in ids]
    for v in vals:score_trace(v,[0])
    cc=shutil.which(a.compiler) or (a.compiler if Path(a.compiler).is_file() else None)
    if not cc:raise RuntimeError('C++17 compiler missing: install g++ or pass --compiler absolute_path')
    text=src.read_text(encoding='utf-8-sig')
    if a.mode=='batch':
        if not all(k in text for k in ['bool readNumber(','struct Search {','#ifndef LOCAL_BATCH']):raise ValueError('source not compatible with batch adapter; use pipe')
        lo=text.index('bool readNumber(');hi=text.index('struct Search {')
        text='#define LOCAL_BATCH\n'+text[:lo]+'''static std::vector<long long> actualInput;
static int actualQuery;
bool readNumber(long long& y){y=actualInput.at(actualQuery);return true;}
void emitQuery(int x){actualQuery=x;}
'''+text[hi:]+'''
int main(){int count,n;if(scanf("%d",&count)!=1)return 2;
while(count--){if(scanf("%d",&n)!=1)return 2;actualInput.resize(n);
for(auto& y:actualInput)if(scanf("%lld",&y)!=1)return 2;
Search s(n);s.solve();for(int x:s.trace)printf("%d ",x);puts("");}return 0;}
'''
    cpp=out/'compiled_source.cpp';cpp.write_text(text,encoding='utf-8');exe=out/'runner.exe'
    command([cc,'-std=c++17','-O2','-Wall','-Wextra','-Wpedantic',cpp,'-o',exe],out/'compile')
    if a.mode=='batch':
        payload=str(len(vals))+'\n'+''.join(str(len(v))+'\n'+' '.join(map(str,v))+'\n' for v in vals)
        (out/'batch_input.txt').write_text(payload,encoding='utf-8')
        r=command([exe],out/'run',payload)
        if r.stderr:raise RuntimeError('unexpected batch stderr')
        traces=[list(map(int,l.split())) for l in r.stdout.splitlines()]
        if len(traces)!=len(vals):raise RuntimeError('missing case traces')
    else:traces=[pipe(exe,v,out/f'pipe_{i}.json') for i,v in zip(ids,vals)]
    metrics=[score_trace(v,t) for v,t in zip(vals,traces)]
    save(out/'traces.json',traces);save(out/'metrics.json',[dict(row=i,**m) for i,m in zip(ids,metrics)])
    summary=dict(source=str(src),source_sha256=sha(src),cases=str(cp),cases_sha256=sha(cp),mode=a.mode,rows=ids,total_score=sum(m['score'] for m in metrics),positive=sum(m['score']>0 for m in metrics),exact_positive=sum(m['score']>0 and m['d']==0 for m in metrics),max_Q=max(m['q'] for m in metrics),max_R=max(m['R'] for m in metrics),official_score_prediction=None,warning='Synthetic sum is not an official 102-case score. Same-data per-trace R30 scoring only.')
    save(out/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
