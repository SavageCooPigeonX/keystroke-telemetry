"""探p_ur_s024_v003_d0331_读唤任_λI_load_api_key_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 11 lines | ~101 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _load_api_key(root: Path) -> str | None:
    env = root / '.env'
    if not env.exists():
        return None
    for line in env.read_text('utf-8').splitlines():
        if line.startswith('GEMINI_API_KEY='):
            return line.split('=', 1)[1].strip()
    return None
