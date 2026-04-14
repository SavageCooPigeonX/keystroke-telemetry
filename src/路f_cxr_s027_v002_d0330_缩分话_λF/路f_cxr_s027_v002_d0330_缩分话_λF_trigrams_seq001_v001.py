"""路f_cxr_s027_v002_d0330_缩分话_λF_trigrams_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 6 lines | ~71 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _trigrams(text: str) -> set[str]:
    words = re.findall(r'\b\w{3,}\b', text.lower())
    return set(f'{words[i]} {words[i+1]} {words[i+2]}' for i in range(len(words) - 2))
