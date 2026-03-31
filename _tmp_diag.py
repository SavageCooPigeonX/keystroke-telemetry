"""Diagnose why enricher isn't firing and check journal + training pairs."""
import json, os, re
from datetime import datetime, timezone

# 1. Check enricher block staleness
cp = open('.github/copilot-instructions.md', 'r', encoding='utf-8').read()
m = re.search(r'<!-- pigeon:current-query -->(.*?)<!-- /pigeon:current-query -->', cp, re.DOTALL)
if m:
    block = m.group(1).strip()
    # Find the "Enriched" timestamp
    em = re.search(r'Enriched (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)', block)
    print(f"=== Enricher block ===")
    print(f"  Last enriched: {em.group(1) if em else 'unknown'}")
    for line in block.split('\n')[:6]:
        print(f"  {line}")
else:
    print("=== NO enricher block in copilot-instructions.md ===")

print()

# 2. Check prompt journal - last 5 entries
print("=== Prompt Journal (last 5) ===")
jl = 'logs/prompt_journal.jsonl'
if os.path.exists(jl):
    lines = open(jl, 'r', encoding='utf-8').read().strip().splitlines()
    print(f"  Total entries: {len(lines)}")
    for l in lines[-5:]:
        j = json.loads(l)
        ts = j.get('ts', '')[:19]
        msg = j.get('msg', '')[:80]
        sn = j.get('session_n', '?')
        dw = j.get('deleted_words', [])
        print(f"  [{sn}] {ts} | \"{msg}\"")
        if dw:
            print(f"    deleted_words: {dw}")
else:
    print("  NO prompt_journal.jsonl!")

print()

# 3. Check training pairs
print("=== Training Pairs ===")
tp = 'logs/shards/training_pairs.md'
if os.path.exists(tp):
    content = open(tp, 'r', encoding='utf-8').read()
    pair_count = content.count('### `')
    print(f"  File exists, {pair_count} pairs")
    # Show last pair
    pairs = content.split('### `')
    if len(pairs) > 1:
        last = pairs[-1][:300]
        print(f"  Last pair preview: ### `{last}")
else:
    print(f"  {tp} does not exist")

# Also check training_pairs via JSONL
tp2 = 'logs/training_pairs.jsonl'
if os.path.exists(tp2):
    lines = open(tp2, 'r', encoding='utf-8').read().strip().splitlines()
    print(f"  training_pairs.jsonl: {len(lines)} entries")
    if lines:
        last = json.loads(lines[-1])
        print(f"  Last: ts={last.get('ts','')[:19]} prompt={last.get('prompt','')[:60]}")
else:
    print(f"  {tp2} does not exist")

print()

# 4. Check unsaid reconstructions - have any fired recently?
print("=== Unsaid Reconstructions ===")
ur = 'logs/unsaid_reconstructions.jsonl'
if os.path.exists(ur):
    lines = open(ur, 'r', encoding='utf-8').read().strip().splitlines()
    print(f"  Total: {len(lines)}")
    for l in lines[-3:]:
        r = json.loads(l)
        ts = r.get('ts', '')[:19]
        trigger = r.get('trigger', '?')
        intent = r.get('reconstructed_intent', '')[:100]
        print(f"  [{trigger}] {ts} | {intent}")
else:
    print("  NO unsaid_reconstructions.jsonl!")

print()

# 5. Check what calls the enricher
print("=== Enricher call chain ===")
# The enricher is called from prompt_journal's log_enriched_entry
# Which is invoked by the mandatory command in copilot-instructions.md
# But that command requires Copilot to run it manually each turn
print("  enricher <- prompt_journal.log_enriched_entry() <- mandatory py -c command")
print("  The enricher ONLY fires when Copilot runs the prompt journal command.")
print("  If that command isn't running, enricher never updates.")
print()

# 6. Check if classify_bridge also fires the enricher
cb = open('vscode-extension/classify_bridge.py', 'r', encoding='utf-8').read()
if 'enricher' in cb.lower() or 'inject_query_block' in cb:
    print("  classify_bridge DOES reference enricher")
else:
    print("  classify_bridge does NOT call enricher — gap!")
    
# Check classify_bridge for enricher calls
if 'prompt_enricher' in cb:
    print("  classify_bridge imports prompt_enricher")
else:
    print("  classify_bridge does NOT import prompt_enricher — enricher only fires from journal cmd")

print()

# 7. Check latest compositions for the recent prompts
print("=== Latest compositions (ts + final_text) ===")
comp = 'logs/chat_compositions.jsonl'
if os.path.exists(comp):
    lines = open(comp, 'r', encoding='utf-8').read().strip().splitlines()[-5:]
    for l in lines:
        c = json.loads(l)
        ts = c.get('ts', '')[:19]
        ft = c.get('final_text', '')[:80]
        dr = c.get('deletion_ratio', 0)
        print(f"  {ts} dr={dr:.3f} | \"{ft}\"")
