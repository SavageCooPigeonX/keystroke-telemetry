"""Show the 8 actual hardcoded imports."""
import re
from pathlib import Path

root = Path('.')
pat = re.compile(r'(from|import)\s+([\w.]*_seq\d+_v\d+_d\d+__[\w]+)')

for py in sorted(root.rglob('*.py')):
    if '.git' in py.parts or '__pycache__' in py.parts or '.venv' in py.parts:
        continue
    rel = str(py.relative_to(root)).replace('\\', '/')
    if rel.startswith('build/'):
        continue
    try:
        text = py.read_text('utf-8')
    except Exception:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if pat.search(line):
            print(f'{rel}:{i}')
            print(f'  {line.strip()[:120]}')
            print()
