"""tc_profile_seq001_v001_section_classify_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 30 lines | ~291 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import time

from .p_tpc_s001_v001 import _SECTION_SIGNALS

_current_section = 'unknown'
_section_enter_time = 0.0

def classify_section(buffer: str, state: str = 'unknown',
                     del_ratio: float = 0.0, wpm: float = 0.0,
                     modules_mentioned: list[str] | None = None) -> str:
    """Classify the current behavioral section from live signals.

    Returns section name. Updates global tracking for entry/exit detection.
    """
    global _current_section, _section_enter_time
    words = set(buffer.lower().split())
    scores: dict[str, float] = {}
    for section, cfg in _SECTION_SIGNALS.items():
        s = len(words & cfg['words']) * 1.5
        s += cfg.get('state_boost', {}).get(state, 0)
        boost = cfg.get('del_ratio_boost', 0)
        if boost > 0:
            s += del_ratio * boost * 3
        elif boost < 0 and del_ratio < 0.1:
            s += 0.3
        scores[section] = s
    best = max(scores, key=scores.get) if scores else 'unknown'
    if scores.get(best, 0) < 0.5:
        best = 'unknown'
    if best != _current_section:
        _section_enter_time = time.time()
    _current_section = best
    return best
