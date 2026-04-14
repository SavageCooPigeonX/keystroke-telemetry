"""Analyze registry compliance."""
import json
from pathlib import Path

reg = json.loads(Path('pigeon_registry.json').read_text(encoding='utf-8'))
files = reg.get('files', [])
print(f'Registry: {len(files)} modules')

# Check token distribution
under_50 = sum(1 for f in files if f.get('tokens', 0) <= 50)
under_200 = sum(1 for f in files if f.get('tokens', 0) <= 200)
under_500 = sum(1 for f in files if f.get('tokens', 0) <= 500)
over_500 = sum(1 for f in files if f.get('tokens', 0) > 500)
over_1000 = sum(1 for f in files if f.get('tokens', 0) > 1000)

print(f'\nToken distribution:')
print(f'  ≤50: {under_50}')
print(f'  ≤200: {under_200}')
print(f'  ≤500: {under_500}')
print(f'  >500: {over_500}')
print(f'  >1000: {over_1000}')

# Largest files
print('\nLargest files:')
sorted_files = sorted(files, key=lambda x: -x.get('tokens', 0))[:15]
for f in sorted_files:
    print(f'  {f["tokens"]} tokens: {f["name"]}')
