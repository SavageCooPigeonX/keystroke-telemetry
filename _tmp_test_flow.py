"""Quick test — verify flow engine + node memory imports work."""
import sys
sys.path.insert(0, '.')
from pathlib import Path

root = Path('.')

# Use package imports (they use relative imports internally)
from pigeon_brain.flow import __init__ as _  # ensure package loads
import importlib, glob

# Find the actual module names
def find_mod(pattern):
    matches = sorted(glob.glob(pattern))
    if not matches:
        return None
    p = Path(matches[-1])
    return p.stem

fe_stem = find_mod('pigeon_brain/flow/流f_fe*')
nm_stem = find_mod('pigeon_brain/flow/存p_nm*')
print(f'flow_engine stem: {fe_stem}')
print(f'node_memory stem: {nm_stem}')

# Import via package
fe_mod = importlib.import_module(f'pigeon_brain.flow.{fe_stem}')
nm_mod = importlib.import_module(f'pigeon_brain.flow.{nm_stem}')
print(f'run_flow: {fe_mod.run_flow}')

# Node memory
mem = nm_mod.load_memory(root)
print(f'node_memory: {len(mem)} nodes')
for k in list(mem.keys())[:5]:
    p = mem[k].get('policy', {})
    rs = p.get('rolling_score', '?')
    sc = p.get('sample_count', '?')
    print(f'  {k}: rolling={rs}, samples={sc}')

# test a minimal flow
print('\n--- TEST FLOW ---')
try:
    gd = fe_mod.load_graph_data(root)
    print(f'graph nodes: {len(gd.get("nodes", {}))}')
    packet = fe_mod.run_flow(root, 'overcap bug - files are too large', mode='failure')
    print(f'path: {packet.path}')
    print(f'accumulated: {len(packet.accumulated)} nodes')
    print(f'fears: {packet.fear_chain[:3]}')
    print(f'dead_vein_warnings: {packet.dead_vein_warnings[:3]}')
except Exception as e:
    print(f'flow error: {e}')
    import traceback; traceback.print_exc()
