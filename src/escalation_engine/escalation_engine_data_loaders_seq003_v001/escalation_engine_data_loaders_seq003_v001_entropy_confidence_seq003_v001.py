"""escalation_engine_data_loaders_seq003_v001_entropy_confidence_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 23 lines | ~212 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _load_entropy_confidence(root: Path) -> dict:
    """Load entropy map → per-module confidence (1 - entropy).
    Returns: {module_name: confidence_float}
    """
    fp = root / 'logs' / 'entropy_map.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result = {}
    for m in data.get('top_entropy_modules', []):
        name = m.get('module', '')
        entropy = m.get('avg_entropy', 0.5)
        shed = m.get('shed_avg_confidence')
        conf = shed if shed is not None else (1.0 - entropy)
        result[name] = conf
    return result
