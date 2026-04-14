"""环检p_ld_s005_v002_d0323_缩描意_λP_fingerprint_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 8 lines | ~92 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _path_fingerprint(path: list[str]) -> str:
    """Stable fingerprint for an execution path."""
    # Strip version info, keep module names
    clean = [re.sub(r'_seq\d+.*$', '', f).strip() for f in path]
    return " → ".join(clean[-6:])  # last 6 hops
