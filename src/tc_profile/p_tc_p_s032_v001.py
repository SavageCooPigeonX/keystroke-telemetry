"""tc_profile_seq001_v001_update_composition_decomposed_seq032_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 032 | VER: v001 | 83 lines | ~875 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
import json
import re
import time

def update_profile_from_composition(comp: dict):
    """Update profile from a raw composition event (from chat_compositions.jsonl).

    Normalizes the actual JSONL format (chat_state.signals.wpm, etc.) before
    feeding into the profile shards. Handles both old and new data shapes.
    """
    profile = load_profile()
    s = profile['shards']

    # ── NORMALIZE: chat_compositions.jsonl uses chat_state.signals.wpm,
    # not top-level signals.wpm. Handle both shapes. ──
    chat_state = comp.get('chat_state', {})
    if isinstance(chat_state, dict):
        signals = chat_state.get('signals', comp.get('signals', {}))
        state = chat_state.get('state', comp.get('cognitive_state', 'unknown'))
    else:
        signals = comp.get('signals', {})
        state = comp.get('cognitive_state', 'unknown')

    # --- rhythm shard ---
    rhythm = s['rhythm']
    wpm = signals.get('wpm', 0)
    if wpm > 0:
        n = max(profile['samples'], 1)
        rhythm['avg_wpm'] = round(rhythm['avg_wpm'] * (n-1)/n + wpm/n, 1)
    rhythm['avg_del_ratio'] = round(
        rhythm['avg_del_ratio'] * 0.95 + comp.get('deletion_ratio', 0) * 0.05, 4)

    # --- deletions shard ---
    dels = s['deletions']
    for dw in comp.get('deleted_words', []):
        word = dw if isinstance(dw, str) else dw.get('word', '')
        if word and len(word) > 2:
            dels['deleted_words'][word.lower()] = dels['deleted_words'].get(word.lower(), 0) + 1
    if len(dels['deleted_words']) > 60:
        dels['deleted_words'] = dict(Counter(dels['deleted_words']).most_common(40))
    # top unsaid — complete words that got deleted
    dels['top_unsaid'] = [w for w, c in Counter(dels['deleted_words']).most_common(8)
                          if len(w) > 3]

    # --- emotions shard ---
    emo = s['emotions']
    state = comp.get('cognitive_state', 'unknown')
    sd = emo['state_distribution']
    sd[state] = sd.get(state, 0) + 1
    # normalize to percentages
    total = sum(sd.values())
    emo['avg_hesitation'] = round(
        emo['avg_hesitation'] * 0.95 + signals.get('hesitation_score', 0) * 0.05, 3)

    # ── SECTION + INTELLIGENCE PIPELINE (composition-grade signals) ──
    final_text = comp.get('final_text', '')
    section = classify_section(
        final_text, state=state, del_ratio=comp.get('deletion_ratio', 0),
        wpm=wpm,
    )
    if section != 'unknown' and final_text:
        deleted = comp.get('deleted_words', [])
        del_words = [dw if isinstance(dw, str) else dw.get('word', '') for dw in deleted]
        rewrites = comp.get('rewrite_chains', comp.get('rewrites', []))
        mod_mentions = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)+', final_text.lower())
        hour_utc = datetime.now(timezone.utc).hour
        update_section(
            profile, section, final_text, '', 'composition',
            state=state, wpm=wpm,
            del_ratio=comp.get('deletion_ratio', 0),
            hesitation=signals.get('hesitation_score', signals.get('hesitation_count', 0)),
            deleted_words=del_words,
            rewrite_chains=rewrites[:3],
            modules_mentioned=mod_mentions,
            session_n=comp.get('session_n', 0),
            hour_utc=hour_utc,
        )
    _deduce_intelligence(profile)

    save_profile(profile)
