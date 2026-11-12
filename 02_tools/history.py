"""Browse or restore the losslessly deduplicated historic records after unzip."""
import argparse,hashlib,json,sys
from pathlib import Path,PurePosixPath

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['list','cat','extract','verify']);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--path',default='');p.add_argument('--out');a=p.parse_args()
    root=Path(a.root).resolve();index=json.loads((root/'05_history/history_index.json').read_text(encoding='utf-8'))
    entries=[e for e in index['files'] if not a.path or e['path']==a.path or e['path'].startswith(a.path.rstrip('/')+'/')]
    if not entries:raise ValueError('no matching historical record')
    if a.action=='list':
        for e in entries:print(f"{e['bytes']:>12} {e['path']}")
        return
    if a.action=='cat':
        entries=[e for e in entries if e['path']==a.path]
        if len(entries)!=1:raise ValueError('cat requires exact --path')
    out=None
    if a.action=='extract':
        if not a.out:p.error('extract requires --out NEW_DIRECTORY')
        out=Path(a.out).resolve()
        if out.exists() and any(out.iterdir()):raise ValueError('destination must be new/empty; refusing to overwrite')
        out.mkdir(parents=True,exist_ok=True)
    checked=set();lengths={}
    for e in entries:
        digest=e['sha256']
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('invalid object hash')
        obj=root/'05_history/objects'/digest
        if digest not in checked or a.action!='verify':
            data=obj.read_bytes()
            if len(data)!=e['bytes'] or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('object integrity failure: '+e['path'])
            checked.add(digest)
            lengths[digest]=len(data)
        if lengths[digest]!=e['bytes']:raise ValueError('inconsistent duplicate object size')
        if a.action=='cat':sys.stdout.buffer.write(data);return
        if out:
            rel=PurePosixPath(e['path'])
            if rel.is_absolute() or '..' in rel.parts or any(':' in s for s in rel.parts):raise ValueError('unsafe restore path')
            dest=(out/Path(*rel.parts)).resolve()
            if out not in dest.parents:raise ValueError('restore path escapes destination')
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(data)
    print(json.dumps(dict(status='verified' if a.action=='verify' else 'restored',files=len(entries),unique_objects=len(checked),destination=str(out) if out else None),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
