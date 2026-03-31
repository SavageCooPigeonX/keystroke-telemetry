import sys; sys.path.insert(0, '.')
from pathlib import Path
import json, glob, importlib.util

sf = glob.glob('src/self_fix_seq013*.py')[0]
spec = importlib.util.spec_from_file_location('sf', sf)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

reg = json.loads(Path('pigeon_registry.json').read_text(encoding='utf-8'))
report = mod.run_self_fix(Path('.'), reg)
issues = report.get('issues', [])
print(f'Total issues: {len(issues)}')

by_type = {}
for i in issues:
    t = i.get('type', '?')
    by_type[t] = by_type.get(t, 0) + 1
for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f'  {t}: {c}')

print()
print('--- HIGH severity ---')
for i in issues:
    if i.get('severity', '') == 'HIGH':
        itype = i.get('type', '?')
        ifile = str(i.get('file', '?'))[:80]
        print(f'  [{itype}] {ifile}')
