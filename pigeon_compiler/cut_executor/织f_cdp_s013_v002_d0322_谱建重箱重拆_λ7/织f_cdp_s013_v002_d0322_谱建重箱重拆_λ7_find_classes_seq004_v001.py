"""织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_find_classes_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 7 lines | ~99 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pigeon_compiler.pigeon_limits import PIGEON_MAX

def find_oversized_classes(ether_map: dict) -> list:
    """Return classes that exceed PIGEON_MAX lines."""
    return [c for c in ether_map.get("classes", [])
            if (c.get("end_line", 0) - c.get("start_line", 0) + 1) > PIGEON_MAX]
