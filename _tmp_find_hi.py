"""Temp: find all hardcoded pigeon imports."""
import re
from pathlib import Path

pat = re.compile(r'from\s+src\.\S+_seq\d+\S*\s+import')
root = Path('.')
for f in sorted(root.joinpath('src').rglob('*.py')):
    try:
        txt = f.read_text(encoding='utf-8')
    except Exception:
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        if pat.search(line):
            rel = f.relative_to(root)
            print(f'{rel}:{i}  {line.strip()[:120]}')
