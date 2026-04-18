"""Test the interlink pipeline on real modules."""
from pathlib import Path
from src.interlinker_seq001_v001_seq001_v001 import assess_module, interlink_module, interlink_scan
import json

root = Path('.')

# find small modules to test
candidates = sorted(Path('src').glob('*.py'), key=lambda p: p.stat().st_size)
candidates = [c for c in candidates if not c.name.startswith('_')][:5]

print(f'Testing interlink on {len(candidates)} smallest modules:\n')

for filepath in candidates:
    print(f'--- {filepath.name} ---')
    result = interlink_module(filepath, root)
    print(f'  state: {result["state"]}')
    print(f'  lines: {result["lines"]}')
    print(f'  api:   {result["public_api"]} public functions')
    print(f'  checks:')
    for k, v in result['checks'].items():
        icon = '✓' if v else '✗'
        print(f'    {icon} {k}')
    print(f'  test_passed: {result["test_passed"]}')
    if result.get('test_generated'):
        print(f'  [test auto-generated]')
    if not result['test_passed']:
        print(f'  output: {result["test_output"][:200]}')
    print()

# scan summary
print('=== INTERLINK SCAN ===')
scan = interlink_scan(root)
print(f'Total: {scan["total"]}')
for state in ('interlinked', 'tested', 'compressed', 'baseline'):
    print(f'  {state}: {len(scan[state])}')
print(f'  interlinked %: {scan["interlinked_pct"]}%')
