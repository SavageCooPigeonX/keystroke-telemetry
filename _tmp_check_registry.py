import json
from pathlib import Path
reg = json.loads(Path('pigeon_registry.json').read_text('utf-8'))
files = reg.get('files', [])
# Find heat_map, context_budget, models, etc.
for short in ['heat', 'budget', 'model', 'logger', 'operator_stat', 'reactor', 'self_fix', 'engagement']:
    matches = [f.get('name', '') for f in files if short in f.get('name', '').lower()]
    print(f'{short}: {matches[:5]}')
print(f'\ntotal: {len(files)}')
# Print sample entries
for f in files[:5]:
    print(f"  name={f.get('name','')} path={f.get('path','')}")
