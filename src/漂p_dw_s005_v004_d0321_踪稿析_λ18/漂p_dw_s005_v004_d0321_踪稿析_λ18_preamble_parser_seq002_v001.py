"""漂p_dw_s005_v004_d0321_踪稿析_λ18_preamble_parser_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 20 lines | ~191 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _parse_pigeon_preamble(path: Path) -> dict:
    """Extract @pigeon metadata from the first line of a file."""
    first_line = path.read_text(encoding="utf-8").split("\n", 1)[0]
    meta = {}
    if "# @pigeon:" not in first_line:
        return meta
    raw = first_line.split("# @pigeon:", 1)[1]
    for pair in raw.split("|"):
        pair = pair.strip()
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        meta[k] = v
    return meta
