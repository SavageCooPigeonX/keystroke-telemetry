"""tc_profile_update_section_decomposed_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 121 lines | ~1,352 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
import ast
import re
import time

from .tc_profile_empty_section_decomposed_seq005_v001 import _empty_section

def update_section(profile: dict, section: str, buffer: str, completion: str,
                   outcome: str, state: str = 'unknown', wpm: float = 0.0,
                   del_ratio: float = 0.0, hesitation: float = 0.0,
                   deleted_words: list[str] | None = None,
                   rewrite_chains: list | None = None,
                   modules_mentioned: list[str] | None = None,
                   session_n: int = 0, hour_utc: int = 0):
    """Update the section dossier with new evidence. Every call = more intelligence."""
    sections = profile['shards'].setdefault('sections', {})
    if section not in sections or not isinstance(sections.get(section), dict):
        sections[section] = _empty_section()
    sec = sections[section]
    now = datetime.now(timezone.utc).isoformat()

    sec['visit_count'] += 1
    sec['total_completions'] += 1
    if not sec['first_seen']:
        sec['first_seen'] = now
    sec['last_seen'] = now

    # ── vitals ──
    n = sec['visit_count']
    sec['avg_wpm'] = round(sec['avg_wpm'] * (n-1)/n + wpm/n, 1) if n > 1 else wpm
    sec['avg_del_ratio'] = round(sec['avg_del_ratio'] * (n-1)/n + del_ratio/n, 4) if n > 1 else del_ratio
    sec['avg_hesitation'] = round(sec['avg_hesitation'] * (n-1)/n + hesitation/n, 3) if n > 1 else hesitation
    sec['peak_wpm'] = max(sec.get('peak_wpm', 0), wpm)
    sec['worst_hesitation'] = max(sec.get('worst_hesitation', 0), hesitation)

    # ── emotional fingerprint ──
    sd = sec['state_dist']
    sd[state] = sd.get(state, 0) + 1
    sec['dominant_state'] = max(sd, key=sd.get) if sd else 'unknown'
    # entry/exit tracking
    if sec['visit_count'] == 1 or (sec.get('_prev_section') and sec['_prev_section'] != section):
        sec.setdefault('entry_states', [])
        sec['entry_states'] = (sec['entry_states'] + [state])[-10:]
    sec['_prev_section'] = section
    # state transitions within section
    prev_state = sec.get('_last_state')
    if prev_state and prev_state != state:
        key = f'{prev_state}->{state}'
        trans = sec.setdefault('state_transitions', {})
        trans[key] = trans.get(key, 0) + 1
    sec['_last_state'] = state

    # ── suppression map ──
    if deleted_words:
        sw = sec['suppressed_words']
        for dw in deleted_words:
            w = dw.lower() if isinstance(dw, str) else str(dw).lower()
            if len(w) > 2:
                sw[w] = sw.get(w, 0) + 1
        if len(sw) > 60:
            sec['suppressed_words'] = dict(Counter(sw).most_common(40))
    if rewrite_chains:
        sec['rewrite_chains'] = (sec.get('rewrite_chains', []) + rewrite_chains[-3:])[-10:]
    if outcome == 'abandoned':
        sec['abandon_count'] = sec.get('abandon_count', 0) + 1

    # ── module heat ──
    if modules_mentioned:
        hm = sec['hot_modules']
        for m in modules_mentioned:
            hm[m] = hm.get(m, 0) + 1
        if len(hm) > 40:
            sec['hot_modules'] = dict(Counter(hm).most_common(25))
        sec['module_sequences'] = (sec.get('module_sequences', []) + [modules_mentioned[:5]])[-10:]

    # ── vocabulary fingerprint ──
    iw = sec['intent_words']
    for w in buffer.lower().split():
        if len(w) > 3 and w.isalpha():
            iw[w] = iw.get(w, 0) + 1
    if len(iw) > 80:
        sec['intent_words'] = dict(Counter(iw).most_common(50))
    # catchphrases — multi-word sequences that repeat
    buf_lower = buffer.lower()
    for phrase in sec.get('catchphrases', []):
        pass  # detection happens in _deduce_intelligence
    # question patterns
    if '?' in buffer or buffer.lower().startswith(('what ', 'how ', 'why ', 'where ', 'when ', 'is ')):
        sec['question_patterns'] = (sec.get('question_patterns', []) + [buffer[:80]])[-10:]

    # ── temporal patterns ──
    hd = sec.setdefault('hour_dist', {})
    hk = str(hour_utc)
    hd[hk] = hd.get(hk, 0) + 1
    sec['session_depth_avg'] = round(
        sec['session_depth_avg'] * (n-1)/n + session_n/n, 1) if n > 1 else float(session_n)

    # ── completion style ──
    if outcome in ('accepted', 'rewarded'):
        sec['accepted'] += 1
        clen = len(completion)
        sec['avg_accepted_len'] = round(
            sec['avg_accepted_len'] * (sec['accepted']-1)/sec['accepted'] + clen/sec['accepted'], 0)
        sec['working_style'] = (sec.get('working_style', []) + [{
            'buf': buffer[-40:], 'comp': completion[:60], 'len': clen,
        }])[-8:]
        # code vs prose
        code_indicators = sum(1 for sig in ('def ', 'class ', 'import ', '()', ' = ', 'self.')
                              if sig in completion)
        is_code = code_indicators >= 2
        old_ratio = sec.get('code_vs_prose_ratio', 0)
        sec['code_vs_prose_ratio'] = round(old_ratio * 0.9 + (1.0 if is_code else 0.0) * 0.1, 3)
    elif outcome in ('dismissed', 'ignored'):
        clen = len(completion)
        rej = sec['total_completions'] - sec['accepted']
        if rej > 0:
            sec['avg_rejected_len'] = round(
                sec.get('avg_rejected_len', 0) * (rej-1)/rej + clen/rej, 0)
        sec['dead_style'] = (sec.get('dead_style', []) + [{
            'buf': buffer[-40:], 'comp': completion[:40],
        }])[-8:]
