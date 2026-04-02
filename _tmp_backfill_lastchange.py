"""One-time backfill: populate last_change in pigeon_registry.json."""
import json

reg = json.loads(open('pigeon_registry.json', 'r', encoding='utf-8').read())

# Load latest edit_why per file from pulse harvest
whys = {}
try:
    for line in open('logs/edit_pairs.jsonl', 'r', encoding='utf-8'):
        if not line.strip():
            continue
        d = json.loads(line)
        f = d.get('file', '')
        w = d.get('edit_why', '')
        if f and w and w != 'None':
            whys[f] = ' '.join(w.split()[:3])
except Exception:
    pass

matched = 0
files = reg['files']
for entry in files:
    path = entry.get('path', '')
    fname = path.split('/')[-1] if '/' in path else path

    # Try exact path match
    why = whys.get(path, '')

    # Try filename-only match
    if not why:
        for ew_path, ew_val in whys.items():
            if ew_path.endswith(fname):
                why = ew_val
                break

    # No fallback — intent field is bulk tags, not per-file changes.
    # last_change only populated from actual pulse EDIT_WHY data.

    if why:
        entry['last_change'] = why
        matched += 1

open('pigeon_registry.json', 'w', encoding='utf-8').write(
    json.dumps(reg, indent=2, ensure_ascii=False)
)

print(f'Backfilled {matched}/{len(files)} entries with last_change')
print()
# Show samples
for entry in files[:10]:
    name = entry.get('name', '')
    lc = entry.get('last_change', '')
    print(f'  {name:40s} | {lc}')
