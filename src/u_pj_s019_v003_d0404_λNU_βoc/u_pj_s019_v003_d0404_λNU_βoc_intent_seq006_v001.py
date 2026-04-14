"""u_pj_s019_v003_d0404_λNU_βoc_intent_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 10 lines | ~83 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _classify_intent(msg: str) -> str:
    """Classify prompt intent from first matching keyword."""
    low = msg.lower()
    for kw, cat in INTENT_MAP.items():
        if kw in low:
            return cat
    return 'unknown'
