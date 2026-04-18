"""escalation_engine_seq001_v001_data_loaders_seq003_v001_bug_persistence_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 21 lines | ~197 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _load_bug_persistence(root: Path) -> dict:
    """Load per-module bug persistence from self_fix_accuracy.json.
    Returns: {module_name: {type, appearances, status, persistence, recent_ratio}}
    """
    fp = root / 'logs' / 'self_fix_accuracy.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result = {}
    for entry in data.get('persistent_top_10', []):
        mod = entry.get('module', '')
        if mod:
            result.setdefault(mod, []).append(entry)
    return result
