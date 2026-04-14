"""漂p_dw_s005_v004_d0321_踪稿析_λ18_line_count_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 5 lines | ~55 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())
