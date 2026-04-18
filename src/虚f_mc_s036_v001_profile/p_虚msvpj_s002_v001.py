"""虚f_mc_s036_v001_profile_jload_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 11 lines | ~78 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _jload(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception:
        return None
