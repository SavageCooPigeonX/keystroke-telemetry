"""escalation_engine_data_loaders_seq003_v001_registry_files_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 27 lines | ~244 tokens
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
