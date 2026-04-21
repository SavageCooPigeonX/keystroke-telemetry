"""Debug script: test overwriter raw API response."""
import sys, json, time
sys.path.insert(0, '.')
from pathlib import Path
import importlib.util

f = sorted(Path('src').glob('file_overwriter*.py'))[-1]
spec = importlib.util.spec_from_file_location('fo', f)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

pending = m.pending_overwrites()
entry = pending[0]
stem = entry['file_stem']
intent = entry['intent_preview']

path = m._find_file(stem, Path('.'))
if not path:
    print('file not found:', stem)
    sys.exit(1)

original = path.read_text('utf-8', errors='replace')
print('file:', path.name, '| lines:', len(original.splitlines()), '| chars:', len(original))
print('intent:', intent[:80])

key = m._load_deepseek_key(Path('.'))
user = (
    f'INTENT: {intent[:200]}\n\n'
    f'GRADE REASON: {entry.get("reason","")[:200]}\n\n'
    f'FILE PATH: {path}\n\n'
    f'FILE SOURCE (full):\n```python\n{original}\n```\n\n'
    f'Output search-replace blocks for the minimal change that fulfils the intent.'
)

t0 = time.perf_counter()
raw = m._call_deepseek(m._PATCH_SYSTEM, user, key)
print(f'DeepSeek time: {time.perf_counter()-t0:.1f}s')
print()
print('=== RAW RESPONSE ===')
print(raw[:2000])
print()
blocks = m._parse_search_replace_blocks(raw)
print(f'blocks found: {len(blocks)}')
for i, (s, r) in enumerate(blocks):
    print(f'  block {i+1}:')
    print(f'    SEARCH ({len(s)} chars): {repr(s[:80])}')
    found = s in original
    print(f'    in_file: {found}')
    if not found:
        # show first 30 chars of each line and check each
        for ln in s.splitlines()[:3]:
            in_orig = any(ln in ol for ol in original.splitlines())
            print(f'      line in file: {in_orig} | {repr(ln[:60])}')
