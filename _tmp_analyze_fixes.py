"""Analyze and auto-fix hardcoded imports."""
import json, importlib.util, sys, re
from pathlib import Path

# Load self-fix monolith
spec = importlib.util.spec_from_file_location(
    "sf", Path("src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc.py"))
sf = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sf
spec.loader.exec_module(sf)

root = Path('.')
reg = json.loads(root.joinpath('pigeon_registry.json').read_text('utf-8'))
report = sf.run_self_fix(root, reg)

# Analyze hardcoded imports by directory
by_dir = {}
by_file = {}
for p in report['problems']:
    if p['type'] != 'hardcoded_import':
        continue
    f = p.get('file', '?')
    d = f.split('/')[0]
    by_dir[d] = by_dir.get(d, 0) + 1
    by_file[f] = by_file.get(f, 0) + 1

print('Hardcoded imports by directory:')
for d, c in sorted(by_dir.items(), key=lambda x: -x[1]):
    print(f'  {d}: {c}')

print(f'\nTop files ({len(by_file)} total):')
for f, c in sorted(by_file.items(), key=lambda x: -x[1])[:15]:
    print(f'  {c:3d} {f}')

# Now run auto-apply on src/ and pigeon_brain/
print('\n--- Auto-applying import fixes ---')
results = sf.auto_apply_import_fixes(root, dry_run=True)
print(f'Would fix {len(results)} imports')
for r in results[:5]:
    print(f"  {r['file']}: {r['old_import'][:60]}")
    print(f"    -> {r['new_expr'][:60]}")
