"""Find ALL broken relative imports in compliance_seq008 — including non-flagged ones."""
import re
from pathlib import Path

d = Path('pigeon_compiler/rename_engine/compliance_seq008')
pat = re.compile(r'from \.(compliance_seq008[\w]+) import')

for py in sorted(d.glob('*.py')):
    if py.name == '__init__.py':
        continue
    text = py.read_text('utf-8')
    for m in pat.finditer(text):
        print(f'{py.name}: from .{m.group(1)[:80]}...')
