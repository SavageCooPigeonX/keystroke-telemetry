"""git_plugin_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .git_plugin_seq002_v001 import _intent_code_numeric
from .git_plugin_seq003_v001 import _mint_bug_entity
from .git_plugin_seq003_v001 import _ordered_bug_keys
from datetime import datetime, timezone
import ast
import re

def _sync_bug_metadata(entry: dict, current_keys: list[str], today: str) -> None:
    current_keys = _ordered_bug_keys(current_keys)
    previous_keys = _ordered_bug_keys(entry.get('bug_keys', []))
    counts = {
        str(key): int(val)
        for key, val in (entry.get('bug_counts') or {}).items()
        if str(key)
    }
    entities = {
        str(key): str(val)
        for key, val in (entry.get('bug_entities') or {}).items()
        if str(key) and str(val)
    }
    for key in current_keys:
        counts[key] = counts.get(key, 0) + 1
        entities.setdefault(key, _mint_bug_entity(entry.get('name', ''), key))
    if current_keys and (current_keys != previous_keys or not entry.get('last_bug_mark')):
        entry['last_bug_mark'] = f'd{today}v{entry.get("ver", 0):03d}'
    else:
        entry.setdefault('last_bug_mark', '')
    entry['bug_keys'] = current_keys
    entry['bug_counts'] = {key: counts[key] for key in sorted(counts)}
    entry['bug_entities'] = {key: entities[key] for key in sorted(entities)}


def _build_box(entry: dict, h: str, lines: int, tokens: int = 0,
               sessions: int = 0) -> str:
    intent = entry.get("intent") or "(none)"
    intent_code = _intent_code_numeric(intent)
    return (
        f'# ── pigeon ────────────────────────────────────\n'
        f'# SEQ: {entry["seq"]:03d} | VER: v{entry["ver"]:03d} | {lines} lines | ~{tokens:,} tokens\n'
        f'# DESC:   {entry.get("desc") or "(none)"}\n'
        f'# INTENT: {intent} [{intent_code}]\n'
        f'# LAST:   {datetime.now(timezone.utc).strftime("%Y-%m-%d")} @ {h}\n'
        f'# SESSIONS: {sessions}\n'
        f'# ──────────────────────────────────────────────\n'
    )
