"""escalation_engine_seq001_v001_registry_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 33 lines | ~289 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _load_registry_files(root: Path) -> dict:
    """Load registry → {module_desc: {path, name, ver, tokens, bug_keys, history}}.
    Key is the desc (human-readable) to match against dossier/accuracy module names.
    """
    fp = root / 'pigeon_registry.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    files = data if isinstance(data, list) else data.get('files', [])
    result = {}
    for entry in files:
        if isinstance(entry, str):
            continue
        desc = entry.get('desc', '')
        name = entry.get('name', '')
        if desc:
            result[desc] = entry
        if name and name != desc:
            result[name] = entry
    return result


def _has_rollback_version(entry: dict) -> bool:
    """Check if a module has a previous version to rollback to."""
    history = entry.get('history', [])
    return len(history) >= 1 and entry.get('ver', 1) > 1
