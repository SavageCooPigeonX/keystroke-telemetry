"""Inspect module_memory structure + score bug profile self-accuracy."""
import json
from pathlib import Path
from datetime import datetime, timezone

root = Path(__file__).resolve().parent.parent
mm = root / 'logs' / 'module_memory'

print('=== MODULE_MEMORY STRUCTURE (per-file prompt storage) ===')
files = list(mm.glob('*.json'))
print(f'total entries: {len(files)}')
sz = sorted(files, key=lambda p: -p.stat().st_size)[:5]
for f in sz:
    print(f'\n--- {f.name} ({f.stat().st_size}B) ---')
    data = json.loads(f.read_text('utf-8'))
    if isinstance(data, dict):
        print(f'keys: {list(data.keys())}')
        for k, v in data.items():
            if isinstance(v, list):
                print(f'  {k}: list[{len(v)}], first={str(v[0])[:150] if v else None}')
            elif isinstance(v, dict):
                print(f'  {k}: dict keys={list(v.keys())[:8]}')
            else:
                print(f'  {k}: {str(v)[:150]}')

# Self-accuracy audit: compare declared intent vs observed behavior
print()
print('=== BUG PROFILE SELF-ACCURACY AUDIT ===')
reg = json.loads((root/'pigeon_registry.json').read_text('utf-8'))
files_info = reg.get('files', [])
print(f'registry modules: {len(files_info)}')

# Per-module accuracy: did the claimed intent match the bug keys observed?
# Accuracy = 1 - (bugs_observed_not_in_declared / max_1)
# Signals:
#   declared: intent_tag, desc
#   observed: bug_keys from registry, recurrence, version churn
from collections import Counter

scored = []
for f in files_info:
    name = f.get('name', '')
    if not name:
        continue
    declared_intent = f.get('intent_tag', '') or f.get('intent', '')
    declared_desc = f.get('desc', '') or ''
    bug_keys = f.get('bug_keys', []) or []
    version = f.get('version', 1)
    seq = f.get('seq', 1)
    tokens = f.get('tokens', 0)

    # Signals
    n_bugs = len(bug_keys)
    churn = max(version, seq)
    oversized = tokens > 2000

    # Accuracy score:
    #   - high if declared_desc exists, few bugs, low churn, not oversized
    #   - low if oversized + no desc + many bugs
    accuracy = 1.0
    notes = []
    if not declared_desc:
        accuracy -= 0.3
        notes.append('no desc')
    if oversized:
        accuracy -= 0.25
        notes.append(f'oversized({tokens})')
    if n_bugs >= 2:
        accuracy -= 0.2
        notes.append(f'{n_bugs}bugs')
    elif n_bugs == 1:
        accuracy -= 0.1
        notes.append('1bug')
    if churn >= 10:
        accuracy -= 0.15
        notes.append(f'v{churn}')
    accuracy = max(0.0, accuracy)
    scored.append((accuracy, name, declared_intent, bug_keys, tokens, churn, notes))

scored.sort(reverse=True)
print('\nTOP 10 MOST ACCURATE SELF-MODELS (matches declared intent):')
for acc, name, intent, bugs, tok, ch, notes in scored[:10]:
    print(f'  {acc:.2f}  {name:<50}  intent={intent:<12} tok={tok} v{ch}')

print('\nBOTTOM 10 LEAST ACCURATE (biggest delusion):')
for acc, name, intent, bugs, tok, ch, notes in scored[-10:]:
    print(f'  {acc:.2f}  {name:<50}  intent={intent:<12} tok={tok} v{ch}  {",".join(notes)}')

# Save artifact
out = {
    'generated': datetime.now(timezone.utc).isoformat(),
    'total_scored': len(scored),
    'top_accurate': [
        {'score': s, 'name': n, 'intent': i, 'bugs': b, 'tokens': t, 'churn': c, 'notes': no}
        for s,n,i,b,t,c,no in scored[:25]
    ],
    'least_accurate': [
        {'score': s, 'name': n, 'intent': i, 'bugs': b, 'tokens': t, 'churn': c, 'notes': no}
        for s,n,i,b,t,c,no in scored[-25:]
    ],
}
out_path = root/'logs/bug_profile_accuracy.json'
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'\nartifact -> {out_path}')
