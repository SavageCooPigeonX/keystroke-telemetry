"""Deep analysis of sim results — find deeper bugs + build readable report."""
import json, sys, re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path('.')

# Load latest sim results
results = []
for f in ['logs/sim_results_deep_fix.jsonl', 'logs/sim_results_post_bugfix.jsonl', 'logs/sim_results_post_fix.jsonl']:
    p = ROOT / f
    if p.exists():
        with open(p, 'r', encoding='utf-8') as fh:
            for line in fh:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except Exception:
                        pass
        print(f'{f}: {len(results)} entries loaded')
        break

if not results:
    print('no sim results found')
    sys.exit(1)


# ── PART 1: Messages to operator ────────────────────────────────────────────

print('\n' + '='*70)
print('  MESSAGES TO YOU (what the thought completer said)')
print('='*70)

for i, r in enumerate(results):
    buf = r.get('buffer', '')
    pred = r.get('prediction', '')
    actual = r.get('actual', '')
    ov = r.get('word_overlap', 0)
    ctx = r.get('context_files', [])
    latency = r.get('latency_ms', 0)
    
    if not pred.strip():
        continue
    
    # Quality tag
    if ov > 0.15: tag = '✨ GOOD'
    elif ov > 0.08: tag = '🤷 MEH'
    elif ov > 0.03: tag = '😬 OFF'
    elif actual.strip(): tag = '💀 MISS'
    else: tag = '⚪ N/A'
    
    print(f'\n  [{tag}] pause #{i+1} ({latency}ms)')
    print(f'  you typed:  "...{buf[-50:]}"')
    print(f'  AI said:    "{pred[:70]}"')
    if actual.strip():
        print(f'  you meant:  "{actual[:70]}"')
    if ctx:
        print(f'  reading:    {", ".join(ctx[:3])}')


# ── PART 2: Messages to copilot (what context was sent) ──────────────────────

print('\n\n' + '='*70)
print('  MESSAGES TO COPILOT (what context was injected)')
print('='*70)

# Aggregate context file usage
ctx_usage = Counter()
ctx_overlaps = defaultdict(list)
for r in results:
    for f in r.get('context_files', []):
        ctx_usage[f] += 1
        ctx_overlaps[f].append(r.get('word_overlap', 0))

print('\n  context files ranked by usage:')
for f, count in ctx_usage.most_common(15):
    avg_ov = sum(ctx_overlaps[f]) / len(ctx_overlaps[f]) if ctx_overlaps[f] else 0
    tag = '🔴' if avg_ov < 0.05 else ('🟡' if avg_ov < 0.1 else '🟢')
    print(f'    {tag} {f}: {count}x used, avg overlap={avg_ov:.1%}')


# ── PART 3: Missing context — what SHOULD have been injected ─────────────────

print('\n\n' + '='*70)
print('  MISSING CONTEXT (what the AI needed but didn\'t have)')
print('='*70)

# Analyze what words appeared in actual text but not in predictions
for i, r in enumerate(results):
    pred = r.get('prediction', '').lower()
    actual = r.get('actual', '').lower()
    buf = r.get('buffer', '').lower()
    ctx = r.get('context_files', [])
    
    if not actual.strip() or not pred.strip():
        continue
    
    actual_words = set(re.findall(r'[a-z_]{4,}', actual))
    pred_words = set(re.findall(r'[a-z_]{4,}', pred))
    buf_words = set(re.findall(r'[a-z_]{4,}', buf))
    
    # Words in actual that weren't in prediction OR buffer
    truly_missed = actual_words - pred_words - buf_words
    # Filter out common filler
    filler = {'this', 'that', 'with', 'from', 'have', 'what', 'then', 'they',
              'their', 'will', 'would', 'could', 'should', 'about', 'also',
              'just', 'like', 'more', 'still', 'feel', 'think', 'going',
              'doesnt', 'doing', 'were', 'been'}
    truly_missed -= filler
    
    if truly_missed and r.get('word_overlap', 0) < 0.1:
        print(f'\n  pause #{i+1}: missed concepts = {", ".join(sorted(truly_missed)[:8])}')
        print(f'    buffer: "...{buf[-45:]}"')
        print(f'    actual: "{actual[:60]}"')
        print(f'    context was: {", ".join(ctx[:3]) if ctx else "(none)"}')


# ── PART 4: Deep bug diagnosis ───────────────────────────────────────────────

print('\n\n' + '='*70)
print('  DEEP BUG DIAGNOSIS')
print('='*70)

bugs = []

# Bug: prediction topic vs buffer topic mismatch
topic_mismatches = 0
for r in results:
    buf = r.get('buffer', '').lower()
    pred = r.get('prediction', '').lower()
    actual = r.get('actual', '').lower()
    if not actual.strip() or not pred.strip():
        continue
    
    # Check if prediction talks about something completely unrelated to buffer
    buf_keywords = set(w for w in re.findall(r'[a-z_]{5,}', buf)
                       if w not in {'would', 'could', 'should', 'about', 'think',
                                   'maybe', 'probably', 'really', 'going', 'doing'})
    pred_keywords = set(w for w in re.findall(r'[a-z_]{5,}', pred)
                       if w not in {'would', 'could', 'should', 'about', 'think',
                                   'maybe', 'probably', 'really', 'going', 'doing'})
    if buf_keywords and pred_keywords:
        shared = buf_keywords & pred_keywords
        if not shared:
            topic_mismatches += 1

non_empty = sum(1 for r in results if r.get('actual', '').strip() and r.get('prediction', '').strip())
if topic_mismatches > non_empty * 0.3:
    bugs.append({
        'id': 'topic_drift',
        'certainty': 0.85,
        'desc': f'{topic_mismatches}/{non_empty} predictions had ZERO keyword overlap with buffer — '
                f'the AI ignores what you\'re actually typing and talks about something else',
        'fix': 'system prompt needs stronger buffer anchoring — "your FIRST word must relate to buffer topic"',
    })

# Bug: echo detection — does the AI repeat codebase signals back?
echo_terms = ['entropy', 'heat map', 'organism', 'copilot focus', 'module fears',
              'rework', 'escalation', 'narrative', 'bug voice', 'prompt composition']
echo_count = 0
for r in results:
    pred = r.get('prediction', '').lower()
    for term in echo_terms:
        if term in pred and term not in r.get('buffer', '').lower():
            echo_count += 1
            break

if echo_count > 3:
    bugs.append({
        'id': 'signal_echo',
        'certainty': 0.90,
        'desc': f'{echo_count}/{non_empty} predictions echoed codebase signals back '
                f'("entropy", "heat map", etc.) — the AI is summarizing its inputs, not predicting typing',
        'fix': 'add post-processing filter that strips known signal vocabulary from completions',
    })

# Bug: generic padding — does the AI produce empty filler?
filler_preds = 0
filler_phrases = ['i think', 'maybe we', 'let me', 'we should', 'we could', 
                  'we need', 'it might', 'perhaps', 'basically', 'i mean']
for r in results:
    pred = r.get('prediction', '').lower().strip()
    if any(pred.startswith(f) for f in filler_phrases):
        filler_preds += 1

if filler_preds > non_empty * 0.2:
    bugs.append({
        'id': 'filler_openings',
        'certainty': 0.75,
        'desc': f'{filler_preds}/{non_empty} predictions start with filler phrases ("i think", "we should") '
                f'— generic opener padding instead of specific continuation',
        'fix': 'post-process: strip standard filler openings, or add system prompt rule against them',
    })

# Bug: prediction too long / chatbot mode
chatbot_count = 0
for r in results:
    pred = r.get('prediction', '')
    if len(pred) > 200:
        chatbot_count += 1

if chatbot_count > non_empty * 0.15:
    bugs.append({
        'id': 'chatbot_mode',
        'certainty': 0.70,
        'desc': f'{chatbot_count}/{non_empty} predictions were >200 chars — '
                f'the AI is writing essays, not autocomplete',
        'fix': 'reduce maxOutputTokens from 400→150, or post-truncate to 80 chars',
    })

# Bug: same opening phrase repeated across predictions
openings = Counter()
for r in results:
    pred = r.get('prediction', '').strip().lower()
    if pred:
        opening = ' '.join(pred.split()[:3])
        openings[opening] += 1

repeated_openings = [(op, c) for op, c in openings.most_common(5) if c >= 3]
if repeated_openings:
    bugs.append({
        'id': 'repetitive_openings',
        'certainty': 0.80,
        'desc': f'Same opening phrases repeated across predictions: '
                f'{", ".join(f"{op}({c}x)" for op, c in repeated_openings[:3])} '
                f'— the model has a crutch vocabulary',
        'fix': 'inject banned openings from ThoughtBuffer history, or vary temperature per position',
    })

# Bug: predictions never reference operator's actual words
buffer_word_usage = 0
for r in results:
    buf = r.get('buffer', '').lower()
    pred = r.get('prediction', '').lower()
    if not pred.strip():
        continue
    buf_important = [w for w in re.findall(r'[a-z_]{5,}', buf)
                     if w not in {'would', 'could', 'should', 'about', 'think',
                                 'maybe', 'probably', 'really'}]
    if buf_important and any(w in pred for w in buf_important):
        buffer_word_usage += 1

if non_empty > 0 and buffer_word_usage / non_empty < 0.4:
    bugs.append({
        'id': 'buffer_ignored',
        'certainty': 0.85,
        'desc': f'Only {buffer_word_usage}/{non_empty} predictions referenced a significant buffer word — '
                f'the AI reads the buffer but doesn\'t anchor predictions to it',
        'fix': 'system prompt needs "your completion MUST contain at least one keyword from the buffer"',
    })

# Bug: context files selected but never used in predictions
ctx_mentioned_in_pred = 0
total_ctx_selections = 0
for r in results:
    pred = r.get('prediction', '').lower()
    for f in r.get('context_files', []):
        total_ctx_selections += 1
        # Check if any part of the context file name appears in prediction
        parts = f.lower().replace('_seq', ' ').split('_')
        meaningful = [p for p in parts if len(p) > 3]
        if any(p in pred for p in meaningful):
            ctx_mentioned_in_pred += 1

if total_ctx_selections > 0 and ctx_mentioned_in_pred / total_ctx_selections < 0.15:
    bugs.append({
        'id': 'context_wasted',
        'certainty': 0.70,
        'desc': f'Only {ctx_mentioned_in_pred}/{total_ctx_selections} context file selections '
                f'were reflected in predictions — the AI reads code context but doesn\'t use it',
        'fix': 'context snippets may be too long/noisy — compress to function signatures only, or '
               'add explicit instruction to USE the code facts',
    })


# ── PART 5: Self-improvement recommendations ────────────────────────────────

print('\n\n' + '='*70)
print('  SELF-IMPROVEMENT RECOMMENDATIONS (ranked by certainty)')
print('='*70)

# Sort bugs by certainty
bugs.sort(key=lambda b: b['certainty'], reverse=True)

for i, bug in enumerate(bugs, 1):
    bar = '█' * int(bug['certainty'] * 10) + '░' * (10 - int(bug['certainty'] * 10))
    print(f'\n  #{i} [{bar}] {bug["certainty"]:.0%} certainty')
    print(f'  🐛 {bug["id"]}: {bug["desc"]}')
    print(f'  💡 fix: {bug["fix"]}')

# Add recommendations from overlap analysis
print('\n\n  --- additional observations ---')
overlaps = [r.get('word_overlap', 0) for r in results if r.get('actual', '').strip()]
if overlaps:
    avg = sum(overlaps) / len(overlaps)
    zeros = sum(1 for o in overlaps if o == 0)
    above10 = sum(1 for o in overlaps if o > 0.1)
    print(f'\n  overall: avg overlap={avg:.1%}, {zeros}/{len(overlaps)} zero, {above10}/{len(overlaps)} above 10%')
    
    # Check if early-in-session is worse than late
    early = [r.get('word_overlap', 0) for r in results[:len(results)//3] if r.get('actual', '').strip()]
    late = [r.get('word_overlap', 0) for r in results[-len(results)//3:] if r.get('actual', '').strip()]
    if early and late:
        early_avg = sum(early) / len(early)
        late_avg = sum(late) / len(late)
        if late_avg > early_avg * 1.3:
            print(f'  📈 accuracy improves over session: early={early_avg:.1%} → late={late_avg:.1%}')
            print(f'     (ThoughtBuffer is learning — the feedback loop works)')
        elif early_avg > late_avg * 1.3:
            print(f'  📉 accuracy DECREASES over session: early={early_avg:.1%} → late={late_avg:.1%}')
            print(f'     (session context accumulation is HURTING predictions — too much noise)')

# Latency analysis 
latencies = [r.get('latency_ms', 0) for r in results if r.get('latency_ms', 0) > 0]
if latencies:
    avg_lat = sum(latencies) / len(latencies)
    slow = sum(1 for l in latencies if l > 1500)
    print(f'\n  latency: avg={avg_lat:.0f}ms, {slow}/{len(latencies)} over 1.5s')
    if avg_lat > 1200:
        print(f'  ⚠️ avg latency above 1.2s — completions arrive after user resumes typing')

print('\n' + '='*70)
