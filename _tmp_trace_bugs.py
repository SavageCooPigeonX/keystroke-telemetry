"""Trace echo and topic drift bugs."""
import json, re
results = [json.loads(l) for l in open('logs/sim_results_post_bugfix.jsonl','r',encoding='utf-8') if l.strip()]

echo_terms = ['entropy', 'heat map', 'organism', 'copilot focus', 'module fears',
              'prompt composition', 'prompt_composition', 'compositions.jsonl', 'bug voice']
print('=== SIGNAL ECHO (AI parrots back its own inputs) ===')
for i, r in enumerate(results):
    pred = r.get('prediction','').lower()
    buf = r.get('buffer','').lower()
    for t in echo_terms:
        if t in pred and t not in buf:
            print(f'  #{i+1}: echoed "{t}"')
            print(f'    pred: "{r["prediction"][:80]}"')
            break

print('\n=== TOPIC DRIFT (prediction topic != buffer topic) ===')
drift_count = 0
for i, r in enumerate(results):
    buf = r.get('buffer','').lower()
    pred = r.get('prediction','').lower()
    actual = r.get('actual','').strip()
    if not pred.strip() or not actual:
        continue
    buf_kw = set(w for w in re.findall(r'[a-z_]{5,}', buf) if w not in 
                 {'would','could','should','about','think','maybe','probably','really','going','doing','thing','being','there'})
    pred_kw = set(w for w in re.findall(r'[a-z_]{5,}', pred) if w not in
                  {'would','could','should','about','think','maybe','probably','really','going','doing','thing','being','there'})
    shared = buf_kw & pred_kw
    if buf_kw and pred_kw and not shared:
        drift_count += 1
        print(f'  #{i+1}: buffer had [{",".join(list(buf_kw)[:5])}] but pred had [{",".join(list(pred_kw)[:5])}]')
        print(f'    buf:  "{buf[-50:]}"')
        print(f'    pred: "{pred[:60]}"')

print(f'\n  total drifts: {drift_count}')

print('\n=== ABANDONED SESSION BUG (same "actual" for many pauses) ===')
# Session 280 has 11 pauses but the buffer was being deleted/rewritten
# The "actual" is always "so thats the best way to fix it..." for pauses 23-33
# This means the sim is comparing predictions against the FINAL buffer,
# not against what was typed NEXT after the pause
actuals = {}
for i, r in enumerate(results):
    a = r.get('actual','')[:40]
    if a:
        actuals.setdefault(a, []).append(i+1)

for a, indices in actuals.items():
    if len(indices) >= 3:
        print(f'  "{a}..." appears as "actual" for pauses {indices}')
        print(f'  → the operator was abandoning and rewriting, but sim uses FINAL text as ground truth')
