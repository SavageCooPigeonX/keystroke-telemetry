"""Full interlink pipeline test — interlink all ready modules."""
from pathlib import Path
from src.interlinker import (
    interlink_module, interlink_scan, build_interlink_report,
    accumulate_shard, load_interlink_db,
)

root = Path('.')

# interlink all compressed modules (under cap, syntax valid)
print('=== INTERLINKING ALL ELIGIBLE MODULES ===\n')
src = root / 'src'
interlinked = 0
tested = 0
failed = 0

for py in sorted(src.glob('*.py')):
    if py.name.startswith('_') or py.name == '__init__.py':
        continue
    result = interlink_module(py, root)
    if result['state'] == 'interlinked':
        interlinked += 1
    elif result['test_passed']:
        tested += 1
    else:
        failed += 1
        if failed <= 3:
            print(f'  ✗ {result["module"]}: {result["test_output"][:100]}')

print(f'\nResults: {interlinked} interlinked, {tested} tested, {failed} failed')
print()

# test shard accumulation
db = load_interlink_db(root)
first_module = next(iter(db.keys()), None)
if first_module:
    accumulate_shard(root, first_module, {
        'type': 'intent',
        'source': 'operator_probe',
        'content': 'operator wants this module to handle edge case X',
    })
    db2 = load_interlink_db(root)
    shards = db2[first_module].get('shards', [])
    print(f'Shard test: {first_module} has {len(shards)} shard(s)')

# build report
report = build_interlink_report(root)
print(f'\nReport preview ({len(report)} chars):')
print(report[:500])

# final scan  
scan = interlink_scan(root)
print(f'\n=== FINAL SCAN ===')
print(f'Total: {scan["total"]}')
for state in ('interlinked', 'tested', 'compressed', 'baseline'):
    n = len(scan[state])
    print(f'  {state}: {n}')
print(f'  interlinked %: {scan["interlinked_pct"]}%')
