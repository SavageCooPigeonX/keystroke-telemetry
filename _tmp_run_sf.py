import json
from pathlib import Path
from src.修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc import run_self_fix, write_self_fix_report, auto_apply_import_fixes

root = Path('.')
reg = json.loads(Path('pigeon_registry.json').read_text(encoding='utf-8'))
report = run_self_fix(root, reg)
probs = report['problems']
print(f'Scan complete: {len(probs)} problems, {report["total_files_scanned"]} files scanned')
by_type = {}
for p in probs:
    by_type.setdefault(p['type'], 0)
    by_type[p['type']] += 1
for k, v in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

# Write report
out = write_self_fix_report(root, report)
print(f'\nReport written: {out}')

# Run auto_apply live
print('\n--- auto_apply_import_fixes (dry_run=False) ---')
fixes = auto_apply_import_fixes(root, dry_run=False)
print(f'Applied: {len(fixes)} hardcoded import fixes')
