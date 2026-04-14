"""净拆f_rcs_s010_v006_d0322_译测编深划_λW_next_seq_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 12 lines | ~116 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _next_seq(folder: Path, stem: str) -> int:
    """Find next available sequence number for a stem in folder."""
    import re as _re
    highest = 0
    for py in folder.glob(f"{stem}_seq*_v*.py"):
        m = _re.search(r"_seq(\d+)_v", py.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return highest + 1
