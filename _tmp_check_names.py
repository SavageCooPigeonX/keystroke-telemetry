import sys; sys.path.insert(0, '.')
from pathlib import Path
from src.module_identity_seq001_v001_seq001_v001 import build_identities
ids = build_identities(Path('.'), include_consciousness=False)
# Find anything matching heat map, file_heat, etc.
matches = [i['name'] for i in ids if 'heat' in i['name'].lower() or 'file_heat' in i['name'].lower()]
print(f'heat matches: {matches}')
# Find anything matching cognitive_reactor
matches2 = [i['name'] for i in ids if 'reactor' in i['name'].lower() or 'cognitive' in i['name'].lower()]
print(f'reactor matches: {matches2}')
# First 20 alphabetically sorted
names = sorted(set(i['name'] for i in ids))
print(f'\ntotal: {len(names)}')
for n in names[:30]:
    print(f'  {n}')
print('...')
# Check if short names exist
for short in ['file_heat_map', 'context_budget', 'models', 'logger', 'operator_stats']:
    found = [n for n in names if short in n]
    print(f'{short}: {found[:3]}')
