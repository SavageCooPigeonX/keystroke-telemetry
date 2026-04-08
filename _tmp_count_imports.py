"""Count hardcoded imports excluding build/."""
import re
from pathlib import Path

root = Path('.')
pat = re.compile(r'(from|import)\s+([\w.]+_seq\d+_v\d+_d\d+__[\w]+)')

counts = {}
for py in root.rglob('*.py'):
    if '.git' in py.parts or '__pycache__' in py.parts or '.venv' in py.parts:
        continue
    rel = str(py.relative_to(root)).replace('\\', '/')
    if rel.startswith('build/'):
        continue
    try:
        text = py.read_text('utf-8')
    except Exception:
        continue
    for m in pat.finditer(text):
        imp = m.group(2)
        pkg = imp.split('.')[0] if '.' in imp else 'relative'
        src_dir = rel.split('/')[0]
        key = f'{src_dir} -> {pkg}'
        counts[key] = counts.get(key, 0) + 1

print('=== HARDCODED IMPORTS (excluding build/) ===')
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')
print(f'TOTAL: {sum(counts.values())}')
