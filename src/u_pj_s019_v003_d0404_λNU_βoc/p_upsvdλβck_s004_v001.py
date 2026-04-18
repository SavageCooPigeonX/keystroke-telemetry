"""u_pj_s019_v003_d0404_λNU_βoc_composition_key_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 14 lines | ~124 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _composition_key(comp: dict) -> str:
    parts = [
        str(comp.get('event_hash', '')),
        str(comp.get('first_key_ts', '')),
        str(comp.get('last_key_ts', '')),
        str(comp.get('ts', '')),
        str(comp.get('total_keystrokes', '')),
        str(comp.get('duration_ms', '')),
        str(comp.get('final_text', ''))[:120],
    ]
    return '|'.join(parts)
