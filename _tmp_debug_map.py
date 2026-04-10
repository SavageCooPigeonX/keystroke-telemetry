import sys, re, json
from pathlib import Path
sys.path.insert(0, '.')
from src.module_identity import build_identities

ids = build_identities(Path('.'))
# Find seq011 in src/
for i in ids:
    p = i.get('path', '')
    stem = Path(p).stem
    parent = str(Path(p).parent)
    m = re.search(r'[_]s(?:eq)?(\d{3})', stem)
    if m and m.group(1) == '011' and parent == 'src':
        print(f"  name={i['name']} path={p}")

# Also check how many have 'src' as parent
src_seqs = {}
for i in ids:
    p = i.get('path', '')
    stem = Path(p).stem
    parent = str(Path(p).parent)
    m = re.search(r'[_]s(?:eq)?(\d{3})', stem)
    if m and parent == 'src':
        src_seqs.setdefault(m.group(1), []).append(i['name'])

print(f"\nsrc/ seq counts: {len(src_seqs)} seqs")
for seq, names in sorted(src_seqs.items())[:15]:
    print(f"  seq{seq}: {names}")
