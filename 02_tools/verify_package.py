"""Verify direct package files; --history also verifies all lossless objects."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--history',action='store_true');a=p.parse_args();root=Path(a.root).resolve()
manifest=json.loads((root/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
entries=manifest['files']
if a.history:
    hist=json.loads((root/'05_history/history_index.json').read_text(encoding='utf-8'));seen=set()
    for e in hist['files']:
        if e['sha256'] not in seen:entries.append(dict(path=e['object'],bytes=e['bytes'],sha256=e['sha256']));seen.add(e['sha256'])
for e in entries:
    path=(root/e['path']).resolve()
    if root not in path.parents:raise ValueError('unsafe manifest path')
    h=hashlib.sha256();n=0
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block);n+=len(block)
    if h.hexdigest()!=e['sha256'] or n!=e['bytes']:raise ValueError('integrity mismatch: '+e['path'])
print(json.dumps(dict(status='verified',checked_files=len(entries),history_included=a.history),ensure_ascii=False))
