"""Find all files with hardcoded 'from src.' imports."""
import os
import re

count = 0
files_with_src = {}
for root, dirs, files in os.walk('src'):
    dirs[:] = [d for d in dirs if d not in {'__pycache__', '.venv'}]
    for f in files:
        if not f.endswith('.py'):
            continue
        p = os.path.join(root, f)
        try:
            with open(p, encoding='utf-8') as fh:
                for i, line in enumerate(fh, 1):
                    if re.match(r'\s*from\s+src\.', line):
                        if p not in files_with_src:
                            files_with_src[p] = []
                        files_with_src[p].append((i, line.rstrip()))
                        count += 1
        except Exception:
            pass

print(f'{count} hardcoded src. imports in {len(files_with_src)} files:')
for p, lines in sorted(files_with_src.items()):
    print(f'  {p}:')
    for num, line in lines:
        print(f'    L{num}: {line}')
