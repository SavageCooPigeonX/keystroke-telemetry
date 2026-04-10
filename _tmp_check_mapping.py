import json; from pathlib import Path
gc = json.loads(Path('pigeon_brain/graph_cache.json').read_text('utf-8', errors='ignore'))
nodes = gc.get('nodes', {})
print(f'total graph nodes: {len(nodes)}')
for k in list(nodes.keys())[:15]:
    n = nodes[k]
    p = n.get('path', '')
    print(f'  graph:{k}  ->  path:{p}')

# Now check: does registry have the path stem?
reg = json.loads(Path('pigeon_registry.json').read_text('utf-8'))
files = reg.get('files', [])
path_to_name = {}
for f in files:
    path_to_name[f.get('path', '')] = f.get('name', '')

# Try to match graph nodes to registry entries via path
print('\n--- MAPPING ---')
mapped = 0
unmapped = 0
for k in list(nodes.keys())[:20]:
    n = nodes[k]
    p = n.get('path', '')
    reg_name = path_to_name.get(p, '')
    if reg_name:
        mapped += 1
        print(f'  {k} -> {reg_name}')
    else:
        unmapped += 1
        print(f'  {k} -> UNMAPPED (path={p})')
print(f'\nmapped: {mapped}, unmapped: {unmapped} (of {len(nodes)})')
