from pathlib import Path
import sys
sys.path.insert(0, 'src')
from entropy_shedding_seq001_v001 import get_high_entropy_targets

tgts = get_high_entropy_targets('.', threshold=0.30, limit=25)
for t in tgts:
    stem = t['module']
    found = None
    for folder in ('src', 'pigeon_compiler', 'pigeon_compiler/git_plugin', 'client', 'scripts'):
        p = Path(folder)
        if not p.exists():
            continue
        m = list(p.glob(f'{stem}*.py'))
        if m:
            found = str(m[0])
            break
        m = list(p.glob(f'*{stem}*.py'))
        if m:
            found = str(m[0])
            break
    red = t['red']
    print(f"{stem:40s} red={red:.3f}  ->  {found}")
