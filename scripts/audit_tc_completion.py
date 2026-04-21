"""Audit thought_completer on two buffer types: comedy vs code.

Calls call_gemini directly (same path as popup /complete endpoint) so we see:
  - what ensemble picks for each buffer
  - what Gemini generates
  - whether training fires
  - delta in numeric surface
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from src.intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import get_stats, predict_files
from src.tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer import call_gemini
from src.tc_context_seq001_v001 import load_context

buffers = [
    ('COMEDY',
     "write a joke about a python developer who renames his files compulsively"),
    ('CODE',
     "def select_context_ensemble(buffer, ctx, max_files=3):\n    # merge numeric and heuristic picks\n    "),
]

print('=' * 70)
print('THOUGHT COMPLETER AUDIT — comedy vs code')
print('=' * 70)

stats_0 = get_stats()
print(f'\nBEFORE: vocab={stats_0["vocab_size"]} files={stats_0["files_tracked"]} touches={stats_0["total_touches"]}')

results = []
for label, buf in buffers:
    print('\n' + '=' * 70)
    print(f'[{label}] buffer:')
    print(f'  "{buf}"')
    print('-' * 70)

    # Snapshot numeric state for this buffer BEFORE the call
    pre_preds = predict_files(buf, top_n=5)
    print(f'  numeric predictions BEFORE:')
    for f, s in pre_preds:
        print(f'    {s:.4f}  {f}')

    # Call Gemini (same path the popup hits)
    print(f'\n  calling Gemini...')
    text, ctx_names = call_gemini(buf)

    print(f'\n  ctx_names (ensemble picks injected into prompt):')
    for n in ctx_names:
        print(f'    - {n}')

    print(f'\n  completion (length={len(text)}):')
    print(f'    """{text}"""')

    # Snapshot AFTER
    post_preds = predict_files(buf, top_n=5)
    pre_map = dict(pre_preds)
    deltas = [(f, s - pre_map.get(f, 0)) for f, s in post_preds]
    deltas.sort(key=lambda x: -x[1])
    print(f'\n  numeric predictions AFTER (deltas > 0 = training happened):')
    for f, d in deltas[:5]:
        marker = '  ↑NEW' if d > 0 and f not in pre_map else (f'  +{d:.4f}' if d > 0 else '')
        print(f'    {post_preds[[p[0] for p in post_preds].index(f)][1]:.4f}  {f}{marker}')

    results.append({'label': label, 'buffer': buf, 'completion': text,
                    'ctx_names': ctx_names})

stats_1 = get_stats()
print('\n' + '=' * 70)
print(f'AFTER: vocab={stats_1["vocab_size"]} files={stats_1["files_tracked"]} touches={stats_1["total_touches"]}')
print(f'delta: +{stats_1["vocab_size"]-stats_0["vocab_size"]} words, '
      f'+{stats_1["files_tracked"]-stats_0["files_tracked"]} files, '
      f'+{stats_1["total_touches"]-stats_0["total_touches"]} touches')

# Compare the two completions
print('\n' + '=' * 70)
print('MODE SWITCH EVIDENCE')
print('=' * 70)
for r in results:
    is_code = 'def ' in r['completion'] or '):' in r['completion'] or 'return' in r['completion']
    print(f'  [{r["label"]}] mode detected: {"CODE" if is_code else "PROSE"}  (completion_len={len(r["completion"])})')
