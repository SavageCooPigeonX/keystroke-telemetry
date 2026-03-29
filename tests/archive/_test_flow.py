"""Quick test: verify keystroke data flow fix."""
from client.chat_composition_analyzer import _read_messages, reconstruct_composition
from pathlib import Path

log_path = Path('logs/os_keystrokes.jsonl')
messages = _read_messages(log_path)
print(f'Messages found: {len(messages)}')

# Show last 10 with deleted words
shown = 0
for i in range(len(messages) - 1, -1, -1):
    m = messages[i]
    comp = reconstruct_composition(m)
    dw = comp['deleted_words']
    rw = comp['rewrites']
    if dw or rw:
        inserts = sum(1 for e in m if e['type'] == 'insert')
        deletes = sum(1 for e in m if e['type'] == 'backspace')
        ft = comp['final_text'][:80]
        print(f'\n  msg {i}: {inserts} ins, {deletes} del, del_ratio={comp["deletion_ratio"]}')
        print(f'    final: "{ft}"')
        if dw:
            print(f'    DELETED WORDS: {[w["word"] for w in dw]}')
        if rw:
            print(f'    REWRITES: {[(r["old"], r["new"]) for r in rw]}')
        shown += 1
        if shown >= 10:
            break

# Stats
all_dw = 0
all_rw = 0
for m in messages:
    comp = reconstruct_composition(m)
    all_dw += len(comp['deleted_words'])
    all_rw += len(comp['rewrites'])
print(f'\n=== TOTALS ===')
print(f'Messages: {len(messages)}')
print(f'Total deleted words: {all_dw}')
print(f'Total rewrites: {all_rw}')
