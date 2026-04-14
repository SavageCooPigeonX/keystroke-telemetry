"""叙p_pn_s012_v006_d0328_初写谱净拆_λR_load_snapshot_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 12 lines | ~117 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import os

def _load_composition_snapshot(root: Path) -> dict | None:
    log = root / 'logs' / 'prompt_compositions.jsonl'
    if not log.exists(): return None
    try:
        lines = log.read_text(encoding='utf-8').strip().splitlines()
        return json.loads(lines[-1]) if lines else None
    except Exception: return None
