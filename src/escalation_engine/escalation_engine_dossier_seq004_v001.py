"""escalation_engine_dossier_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 21 lines | ~167 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _load_dossier(root: Path) -> dict:
    """Load active_dossier.json — per-module bug recurrence.
    Returns: {module_name: {bugs, recur, counts, score}}
    """
    fp = root / 'logs' / 'active_dossier.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result = {}
    for d in data.get('dossiers', []):
        mod = d.get('file', '')
        if mod:
            result[mod] = d
    return result
