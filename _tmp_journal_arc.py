"""Quick script to read prompt journal arc."""
import json

entries = []
with open('logs/prompt_journal.jsonl', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.strip():
            try:
                entries.append(json.loads(line))
            except Exception:
                pass

for e in entries[-10:]:
    n = e.get('session_n', '?')
    intent = e.get('intent', '?')
    cog = e.get('cognitive_state', '?')
    msg = e.get('msg', '')[:80]
    dels = e.get('deleted_words', [])
    rewrites = e.get('rewrites', [])
    sig = e.get('signals', {})
    del_r = sig.get('deletion_ratio', 0)
    hes = sig.get('hesitation_count', 0)
    print(f'#{n} [{intent}/{cog}] del={del_r:.0%} hes={hes}')
    print(f'  "{msg}"')
    if dels:
        print(f'  deleted: {dels}')
    if rewrites:
        print(f'  rewrote: {[(r["old"], r["new"]) for r in rewrites[:2]]}')
    print()
