import json

# 1. What does operator_profile say?
print('=== operator_profile.md ===')
text = open('operator_profile.md', 'r', encoding='utf-8').read()
for line in text.splitlines():
    low = line.lower()
    if any(k in low for k in ['submit', 'deletion', 'dominant', 'total messages']):
        print(f'  {line.strip()[:120]}')

print()

# 2. What does prompt_journal actually show?
print('=== prompt_journal.jsonl (real data) ===')
lines = open('logs/prompt_journal.jsonl', 'r', encoding='utf-8').read().strip().splitlines()
print(f'  Total entries: {len(lines)}')
print(f'  All are real submitted prompts (journal only fires via py -c command)')

print()

# 3. What does chat_compositions show for deletion ratio?
comps = open('logs/chat_compositions.jsonl', 'r', encoding='utf-8').read().strip().splitlines()
ratios = []
for l in comps[-50:]:
    c = json.loads(l)
    dr = c.get('deletion_ratio', 0)
    ratios.append(dr)
avg_dr = sum(ratios) / len(ratios) if ratios else 0
print(f'=== chat_compositions.jsonl (last {len(ratios)}) ===')
print(f'  Avg deletion_ratio: {avg_dr:.3f} ({avg_dr*100:.1f}%)')

# 4. What does prompt_telemetry_latest show?
snap = json.loads(open('logs/prompt_telemetry_latest.json', 'r', encoding='utf-8').read())
rs = snap.get('running_summary', {})
baselines = rs.get('baselines', {})
print(f'  Baseline avg_del from telemetry: {baselines.get("avg_del", "?")}')
print(f'  Running avg_del_ratio: {rs.get("avg_del_ratio", "?")}')

print()

# 5. How does operator_profile count submits?
print('=== operator_profile submit counting ===')
# Check if it counts bg: flushes as submits
import re
for line in text.splitlines():
    if 'analyzed' in line.lower() or 'submit' in line.lower():
        print(f'  {line.strip()[:120]}')
