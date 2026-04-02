import sys; sys.path.insert(0, '.')
from pigeon_compiler.rename_engine import audit_compliance
from pathlib import Path

result = audit_compliance(Path('.'))
total = result.get('total', 0)
compliant = result.get('compliant', 0)
pct = result.get('compliance_pct', 0)
oversize = result.get('oversize', [])

print(f'Compliance audit:')
print(f'  Total files:   {total}')
print(f'  Compliant:     {compliant}  ({pct}%)')
print(f'  Non-compliant: {len(oversize)}')

from collections import Counter
counts = Counter(r.get('status','?') for r in oversize)
for k,v in sorted(counts.items()): print(f'    {k}: {v}')

over_hard = [r for r in oversize if r.get('status') == 'OVER_HARD_CAP']
print(f'\nOVER_HARD_CAP ({len(over_hard)} files):')
for r in sorted(over_hard, key=lambda x: -x.get('lines',0))[:25]:
    print(f"  {r.get('lines',0):>5} lines  {r.get('path','')}")

crit = [r for r in oversize if r.get('status') == 'CRITICAL']
print(f'\nCRITICAL >300 lines ({len(crit)} files):')
for r in sorted(crit, key=lambda x: -x.get('lines',0)):
    print(f"  {r.get('lines',0):>5} lines  {r.get('path','')}")
