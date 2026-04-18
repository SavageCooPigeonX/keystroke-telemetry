"""tc_profile_seq001_v001_update_completion_decomposed_seq031_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 031 | VER: v001 | 141 lines | ~1,533 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
import re
import time

from .tc_profile_seq001_v001_load_save_seq030_v001 import load_profile, save_profile
from .tc_profile_seq001_v001_section_classify_seq006_v001 import classify_section
from .tc_profile_seq001_v001_update_section_decomposed_seq007_v001 import update_section
from .tc_profile_seq001_v001_intelligence_orchestrator_seq024_v001 import _deduce_intelligence

def update_profile_from_completion(buffer: str, completion: str, outcome: str,
                                   context: str = '', repo: str = ''):
    """Incrementally update profile after each completion event."""
    profile = load_profile()
    profile['samples'] += 1
    s = profile['shards']

    # --- voice shard ---
    words = buffer.lower().split()
    voice = s['voice']
    tw = voice['top_words']
    for w in words:
        if len(w) > 2 and w.isalpha():
            tw[w] = tw.get(w, 0) + 1
    # keep top 50
    if len(tw) > 80:
        voice['top_words'] = dict(Counter(tw).most_common(50))
    # bigrams
    bg = voice['bigrams']
    for i in range(len(words) - 1):
        if len(words[i]) > 2 and len(words[i+1]) > 2:
            key = f'{words[i]} {words[i+1]}'
            bg[key] = bg.get(key, 0) + 1
    if len(bg) > 60:
        voice['bigrams'] = dict(Counter(bg).most_common(30))
    # avg words per msg (rolling)
    n = profile['samples']
    voice['avg_words_per_msg'] = round(
        voice['avg_words_per_msg'] * (n-1)/n + len(words)/n, 1)
    voice['uses_caps'] = voice['uses_caps'] or any(c.isupper() for c in buffer[:20])
    # filler words
    fillers = {'like', 'also', 'just', 'basically', 'literally', 'actually',
               'maybe', 'kinda', 'gonna', 'wanna', 'gotta', 'tbh', 'ngl'}
    for w in words:
        if w in fillers:
            voice['filler_words'][w] = voice['filler_words'].get(w, 0) + 1

    # --- topics shard ---
    topics = s['topics']
    mm = topics['module_mentions']
    mod_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{3,}', buffer)
    for mw in mod_words:
        ml = mw.lower()
        if '_' in ml or ml in ('thought', 'completer', 'streaming', 'import',
                                'rewriter', 'compiler', 'entropy', 'profile'):
            mm[ml] = mm.get(ml, 0) + 1
    if len(mm) > 60:
        topics['module_mentions'] = dict(Counter(mm).most_common(40))
    # recent focus
    if words:
        key_words = [w for w in words if len(w) > 4 and w.isalpha()][:3]
        if key_words:
            topics['recent_focus'] = (topics['recent_focus'] + [' '.join(key_words)])[-5:]
    # recurring themes
    themes = topics['recurring_themes']
    theme_keys = {
        'debugging': {'fix', 'bug', 'error', 'broken', 'glitch', 'crash', 'fail'},
        'building': {'build', 'create', 'make', 'implement', 'write', 'add'},
        'testing': {'test', 'verify', 'check', 'run', 'launch', 'relaunch'},
        'auditing': {'audit', 'health', 'entropy', 'compliance', 'drift'},
        'exploring': {'what', 'how', 'why', 'show', 'explain', 'look'},
        'restructuring': {'split', 'refactor', 'rename', 'move', 'reorganize'},
    }
    word_set = set(words)
    for theme, keywords in theme_keys.items():
        if word_set & keywords:
            themes[theme] = themes.get(theme, 0) + 1

    # --- decisions shard ---
    dec = s['decisions']
    dec['total_completions'] += 1
    if outcome in ('accepted', 'rewarded'):
        old_rate = dec['accept_rate']
        dec['accept_rate'] = round(old_rate * (n-1)/n + 1/n, 3)
        # store what worked
        pattern = buffer[-50:].strip()
        dec['accepted_patterns'] = (dec['accepted_patterns'] + [pattern])[-15:]
        if outcome == 'rewarded':
            dec['reward_rate'] = round(
                dec['reward_rate'] * (n-1)/n + 1/n, 3)
        # track sweet spot length
        buf_len = len(buffer)
        dec['sweet_spot_len'] = round(
            dec['sweet_spot_len'] * (n-1)/n + buf_len/n, 0)
    else:
        dec['accept_rate'] = round(dec['accept_rate'] * (n-1)/n, 3)
        pattern = buffer[-50:].strip()
        dec['rejected_patterns'] = (dec['rejected_patterns'] + [pattern])[-10:]

    # --- predictions shard ---
    pred = s['predictions']
    if outcome in ('accepted', 'rewarded'):
        entry = {'buf_tail': buffer[-40:], 'comp_head': completion[:60], 'outcome': outcome}
        pred['working_templates'] = (pred['working_templates'] + [entry])[-20:]
        # operator phrases
        if len(buffer) > 10:
            pred['operator_phrases'] = (pred['operator_phrases'] + [buffer[-60:]])[-15:]
    elif outcome in ('dismissed', 'ignored'):
        entry = {'buf_tail': buffer[-40:], 'comp_head': completion[:40]}
        pred['dead_templates'] = (pred['dead_templates'] + [entry])[-10:]

    # --- code_style shard (incremental from code buffers) ---
    code_indicators = sum(1 for sig in ('def ', 'class ', 'import ', 'self.', ' = ',
                                         '()', 'return ', '    ') if sig in buffer)
    if code_indicators >= 2:
        cs = s.get('code_style', {})
        # learn from accepted code patterns
        if outcome in ('accepted', 'rewarded') and completion:
            combined = buffer + completion
            cp = cs.get('common_patterns', [])
            # extract short patterns from accepted code
            lines = combined.strip().split('\n')
            for line in lines[-3:]:
                stripped = line.strip()
                if stripped and len(stripped) > 10 and len(stripped) < 80:
                    cp.append(stripped)
            cs['common_patterns'] = cp[-20:]
            s['code_style'] = cs

    # ── SECTION + INTELLIGENCE PIPELINE ──
    # Classify what behavioral section this buffer belongs to
    section = classify_section(buffer, state='unknown')
    if section != 'unknown':
        # Extract module mentions from buffer for section tracking
        mod_mentions = [w for w in re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)+', buffer.lower())]
        hour_utc = datetime.now(timezone.utc).hour
        update_section(
            profile, section, buffer, completion, outcome,
            modules_mentioned=mod_mentions,
            hour_utc=hour_utc,
        )
    # Run the deduction engine — discover new secrets every cycle
    _deduce_intelligence(profile)

    save_profile(profile)
