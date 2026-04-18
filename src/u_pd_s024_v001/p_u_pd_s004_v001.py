"""u_pd_s024_v001_load_snapshots_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 13 lines | ~95 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_snapshots(root: Path) -> list[dict]:
    p = root / MUTATIONS_PATH
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text('utf-8'))
        return data.get('snapshots', [])
    except Exception:
        return []
