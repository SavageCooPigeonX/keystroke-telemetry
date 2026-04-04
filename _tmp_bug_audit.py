"""Temporary: audit bug persistence + generate browsable profile."""
import json
from pathlib import Path

root = Path('.')
reg = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))
files = reg.get('files', [])

bug_profiles = {}
for entry in files:
    bug_keys = entry.get('bug_keys', [])
    if not bug_keys:
        continue
    name = entry.get('name', '')
    abbrev = entry.get('abbrev', '')
    key = abbrev or name
    bug_profiles[key] = {
        'name': name,
        'abbrev': abbrev,
        'path': entry.get('path', ''),
        'seq': entry.get('seq', 0),
        'ver': entry.get('ver', 0),
        'tokens': entry.get('tokens', 0),
        'bug_keys': bug_keys,
        'bug_counts': entry.get('bug_counts', {}),
        'bug_entities': entry.get('bug_entities', {}),
        'last_bug_mark': entry.get('last_bug_mark', ''),
        'last_change': entry.get('last_change', ''),
        'intent_code': entry.get('intent_code', ''),
        'dossier_score': entry.get('dossier_score', 0),
        'date': entry.get('date', ''),
    }

print(f"Total modules with bugs: {len(bug_profiles)}")
print()

# Group by bug type
by_bug: dict[str, list] = {}
for key, prof in bug_profiles.items():
    for bk in prof['bug_keys']:
        by_bug.setdefault(bk, []).append(prof)

BUG_LEGEND = {
    'hi': 'hardcoded_import',
    'de': 'dead_export',
    'dd': 'duplicate_docstring',
    'hc': 'high_coupling',
    'oc': 'over_hard_cap',
    'qn': 'query_noise',
}

for bk, entries in sorted(by_bug.items()):
    label = BUG_LEGEND.get(bk, bk)
    print(f"--- {bk} / {label} ({len(entries)} modules) ---")
    for e in sorted(entries, key=lambda x: -sum(x['bug_counts'].values())):
        total_recur = sum(e['bug_counts'].values())
        ds = e['dossier_score']
        ab = e['abbrev'] or e['name']
        lc = e['last_change'][:30] if e['last_change'] else ''
        print(f"  {ab:25s} v{e['ver']:02d} tok={e['tokens']:5d} recur={total_recur} ds={ds:.2f} mark={e['last_bug_mark']} [{lc}]")

# Write full JSON dump for browsable profile
(root / 'logs' / 'bug_profiles.json').write_text(
    json.dumps({
        'generated': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'total_bugged': len(bug_profiles),
        'by_type': {
            bk: {
                'label': BUG_LEGEND.get(bk, bk),
                'count': len(entries),
                'modules': [
                    {
                        'abbrev': e['abbrev'],
                        'name': e['name'],
                        'path': e['path'],
                        'ver': e['ver'],
                        'tokens': e['tokens'],
                        'bug_counts': e['bug_counts'],
                        'bug_entities': e['bug_entities'],
                        'last_bug_mark': e['last_bug_mark'],
                        'last_change': e['last_change'],
                        'dossier_score': e['dossier_score'],
                    }
                    for e in sorted(entries, key=lambda x: -sum(x['bug_counts'].values()))
                ],
            }
            for bk, entries in sorted(by_bug.items())
        },
        'all_profiles': bug_profiles,
    }, indent=2),
    encoding='utf-8',
)
print("\nWrote logs/bug_profiles.json")
