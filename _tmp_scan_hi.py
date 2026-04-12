"""Temp: run scanner directly to see what it flags."""
from pathlib import Path
import re

def _scan(root):
    problems = []
    pat = re.compile(r'(from|import)\s+([\w.]+_seq\d+_v\d+_d\d+__[\w]+)')
    for py in root.rglob('*.py'):
        if '.git' in py.parts or '__pycache__' in py.parts:
            continue
        if py.name == '__init__.py' or py.name.startswith('_test_'):
            continue
        rel = str(py.relative_to(root)).replace('\\', '/')
        if rel.startswith('build/'):
            continue
        try:
            text = py.read_text(encoding='utf-8')
        except Exception:
            continue
        for m in pat.finditer(text):
            line_num = text[:m.start()].count('\n') + 1
            line_text = text.splitlines()[line_num - 1].strip()
            in_docstring = _in_docstring(text, m.start())
            in_comment = line_text.lstrip().startswith('#')
            problems.append({
                'file': rel,
                'line': line_num,
                'import': m.group(2)[:80],
                'in_docstring': in_docstring,
                'in_comment': in_comment,
                'line_text': line_text[:120],
            })
    return problems

def _in_docstring(text, pos):
    """Check if position is inside a triple-quoted string."""
    count_triple_double = text[:pos].count('"""')
    count_triple_single = text[:pos].count("'''")
    return (count_triple_double % 2 == 1) or (count_triple_single % 2 == 1)

r = _scan(Path('.'))
print(f'{len(r)} issues found\n')
for p in r:
    tag = ''
    if p['in_docstring']:
        tag = ' [DOCSTRING]'
    elif p['in_comment']:
        tag = ' [COMMENT]'
    else:
        tag = ' [REAL]'
    print(f'  {p["file"]}:{p["line"]}{tag}')
    print(f'    {p["line_text"][:120]}')
    print()
