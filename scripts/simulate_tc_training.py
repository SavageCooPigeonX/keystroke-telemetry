"""Simulate thought_completer training accelerator.

Without calling Gemini, directly exercise the record_touch path with
heuristic-only picks to verify:
  - touches grow
  - numeric surface starts predicting buffers it couldn't before
  - no runaway self-reinforcement (since training only uses heuristic targets)
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from src.intent_numeric_seq001_v001_seq001_v001 import record_touch, predict_files, get_stats
from src.tc_context_seq001_v001_seq001_v001_agent_seq001_v001_seq001_v001 import select_context_files

ctx = {'unsaid_threads': [], 'hot_modules': [], 'recent_prompts': []}

# Synthetic buffers the operator actually types (from recent prompt_journal)
buffers = [
    "are you sure the prompt pairing is actually learning",
    "i want thought completer to accelerate training",
    "test gemini key after rotation",
    "audit bug profiles numeric encoding",
    "does context select get injected into thought completer",
    "push cycle rename engine self fix escalation",
    "prompt journal storage per file with numeric encoding",
    "literal model of operator cognition from keystroke telemetry",
    "loop 2 needs verified before trusting cognition model",
    "numeric surface learned words bug profiles",
]

print('=== BEFORE training acceleration ===')
stats_before = get_stats()
print(f'vocab={stats_before["vocab_size"]} files={stats_before["files_tracked"]} touches={stats_before["total_touches"]}')

# Baseline predictions for a probe buffer
probe = "are you sure the prompt pairing is actually learning"
before_preds = predict_files(probe, top_n=5)
print(f'\nBEFORE probe "{probe}":')
for f, s in before_preds:
    print(f'  {s:.4f}  {f}')

# Simulate: for each buffer, call select_context_files (heuristic only),
# then train on the top heuristic picks with the buffer as signal.
print(f'\n=== SIMULATING {len(buffers)} thought_completer calls ===')
for buf in buffers:
    heuristic_picks = select_context_files(buf, ctx, max_files=3)
    if heuristic_picks:
        targets = [p['name'] for p in heuristic_picks[:3]]
        synthetic_completion = buf + " — rough completion expanding the thought"
        record_touch(f'{buf} {synthetic_completion}', targets, learning_rate=0.02)
        print(f'  trained: "{buf[:45]:<45}" -> {[t[:30] for t in targets]}')

print('\n=== AFTER training acceleration ===')
stats_after = get_stats()
print(f'vocab={stats_after["vocab_size"]} files={stats_after["files_tracked"]} touches={stats_after["total_touches"]}')
print(f'delta: +{stats_after["vocab_size"]-stats_before["vocab_size"]} words, '
      f'+{stats_after["files_tracked"]-stats_before["files_tracked"]} files, '
      f'+{stats_after["total_touches"]-stats_before["total_touches"]} touches')

# Probe the same buffer — did learning happen?
after_preds = predict_files(probe, top_n=5)
print(f'\nAFTER probe "{probe}":')
for f, s in after_preds:
    print(f'  {s:.4f}  {f}')

# Compare
before_map = dict(before_preds)
after_map = dict(after_preds)
print('\n=== CHANGES ===')
new_files = set(after_map) - set(before_map)
if new_files:
    print(f'NEW predictions: {list(new_files)[:5]}')
stronger = [(f, after_map[f] - before_map.get(f, 0)) for f in after_map if f in before_map]
stronger.sort(key=lambda x: -x[1])
print(f'STRONGER (top 3 weight gains):')
for f, delta in stronger[:3]:
    print(f'  +{delta:.4f}  {f}')
