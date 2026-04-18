"""u_pj_s019_v003_d0404_λNU_βoc_select_composition_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 39 lines | ~460 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import re
from .p_u_pj_s001_v001 import MAX_COMP_AGE_MS, MIN_TEXT_MATCH_SCORE, TIGHT_WINDOW_MS
from .p_upsvdλβcc_s009_v001 import _candidate_compositions
from .p_upsvdλβrb_s008_v001 import _recent_bound_composition_keys

def _select_composition(root: Path, now: datetime, msg: str,
                        session_n: int | None = None) -> dict | None:
    now_ms = int(now.timestamp() * 1000)
    used_keys = _recent_bound_composition_keys(root)
    candidates = _candidate_compositions(root, now_ms, msg)
    for candidate in candidates:
        age = candidate['age_ms']
        score = candidate['match_score']
        # Perfect text match — this IS the right composition, bypass age filter
        if score >= 0.95 and candidate['key'] not in used_keys:
            return candidate
        if age > MAX_COMP_AGE_MS:
            continue
        if score < MIN_TEXT_MATCH_SCORE:
            continue
        if candidate['key'] in used_keys:
            continue
        # ±500ms tight-window override: if the composition was created within
        # 500ms of the journal entry AND score is high, accept unconditionally.
        if age <= TIGHT_WINDOW_MS and score >= 0.8:
            return candidate
        # For looser matches, enforce session_n uniqueness as secondary gate
        # to prevent same-session stale composition from contaminating entries.
        comp_entry = candidate.get('entry', {})
        comp_sn = comp_entry.get('session_n')
        if comp_sn is not None and session_n is not None and comp_sn == session_n - 1:
            # Composition is from the previous session item — valid
            return candidate
        if comp_sn is not None and comp_sn == session_n:
            return candidate
        # No session_n info on the composition — fall through to age check
        if age <= MAX_COMP_AGE_MS:
            return candidate
    return None
