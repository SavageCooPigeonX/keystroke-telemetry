"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_seq_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 7 lines | ~70 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _extract_seq(filename: str) -> str:
    """Extract seq number from pigeon filename."""
    m = re.search(r'_seq(\d+)', filename)
    return m.group(1) if m else ''
