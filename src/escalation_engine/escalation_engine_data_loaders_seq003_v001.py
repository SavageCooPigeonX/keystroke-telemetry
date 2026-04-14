"""escalation_engine_data_loaders_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 92 lines | ~732 tokens
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
