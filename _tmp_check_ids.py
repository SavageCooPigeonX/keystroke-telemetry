import sys, json
from pathlib import Path
sys.path.insert(0, '.')
from src.module_identity import build_identities

ids = build_identities(Path('.'))
# Show src/ identities
src_ids = [i for i in ids if 'src/' in i.get('path', '')]
print(f'{len(src_ids)} src identities:')
for i in src_ids[:25]:
    print(f"  name={i['name']:45s} path={i['path']}")

# Show graph_cache node → path for comparison
print()
gc = json.loads(Path('pigeon_brain/graph_cache.json').read_text('utf-8', errors='ignore'))
nodes = gc.get('nodes', {})
src_nodes = {k: v for k, v in nodes.items() if 'src/' in v.get('path', '')}
print(f'{len(src_nodes)} graph src nodes:')
for k, v in list(src_nodes.items())[:25]:
    print(f"  node={k:45s} path={v['path']}")

# Build mapping: graph node → identity by shared seq number + directory
print('\n--- MAPPING ATTEMPT via seq+dir ---')
id_by_dir_seq = {}
for i in ids:
    p = i.get('path', '')
    stem = Path(p).stem
    # extract seq from _sNNN or _seqNNN
    import re
    m = re.search(r'[_]s(?:eq)?(\d{3})', stem)
    if m:
        seq = m.group(1)
        d = str(Path(p).parent)
        key = (d, seq)
        id_by_dir_seq[key] = i['name']

mapped = 0
for nname, ndata in nodes.items():
    np = ndata.get('path', '')
    nstem = Path(np).stem
    m = re.search(r'[_]s(?:eq)?(\d{3})', nstem)
    if m:
        seq = m.group(1)
        d = str(Path(np).parent)
        key = (d, seq)
        if key in id_by_dir_seq:
            mapped += 1
            if mapped <= 15:
                print(f"  {nname:40s} -> {id_by_dir_seq[key]}")
        else:
            if mapped < 3:
                print(f"  {nname:40s} -> UNMAPPED (dir={d}, seq={seq})")

print(f'\nmapped: {mapped}/{len(nodes)}')
