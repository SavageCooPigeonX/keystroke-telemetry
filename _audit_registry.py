"""Quick registry staleness audit — correct schema: registry['files'] is a list."""
import json
import subprocess
from pathlib import Path

root = Path('.')
data = json.loads((root / 'pigeon_registry.json').read_text('utf-8', errors='ignore'))
files = data.get('files', [])

registered_paths = {f['path'] for f in files}

print(f'Registry: {len(files)} registered | generated: {data.get("generated","?")}')

# ── Unregistered src/*.py ──────────────────────────────────────────────────
src_py = sorted(Path('src').glob('*.py'))
unregistered = [p for p in src_py if not any(p.name in rp for rp in registered_paths)]
print(f'\nUNREGISTERED src/*.py ({len(unregistered)} files):')
for p in unregistered[:20]:
    print(f'  {p.name}')
if len(unregistered) > 20:
    print(f'  ... and {len(unregistered)-20} more')

# ── Over-cap ──────────────────────────────────────────────────────────────
print('\nOVER-CAP (tokens>2000):')
for f in files:
    tok = f.get('tokens', 0) or 0
    if tok > 2000:
        print(f'  {Path(f["path"]).name[:65]}  tokens={tok}  bugs={f.get("bug_keys")}')

# ── Active bugs ────────────────────────────────────────────────────────────
print('\nACTIVE BUGS:')
for f in files:
    bk = f.get('bug_keys', [])
    if bk:
        print(f'  {Path(f["path"]).name[:65]}  {bk}')

# ── Version drift ──────────────────────────────────────────────────────────
print('\nVERSION DRIFT (registered file last_commit != HEAD):')
try:
    head = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
    for f in files:
        last = f.get('last_commit', '') or f.get('last', '')
        fp = root / f['path']
        if last and last != head and fp.exists():
            print(f'  {Path(f["path"]).name[:55]}  last={last}  head={head}')
    print(f'  HEAD={head}')
except Exception as e:
    print(f'  (git error: {e})')

# ── Staged but unregistered ────────────────────────────────────────────────
print('\nSTAGED BUT UNREGISTERED (new to registry after next push):')
try:
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).splitlines()
    for s in staged:
        if s.endswith('.py') and not any(s in rp for rp in registered_paths):
            print(f'  {s}')
except Exception as e:
    print(f'  (git error: {e})')
