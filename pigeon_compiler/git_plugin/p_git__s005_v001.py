"""git_plugin_bug_metadata_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 53 lines | ~526 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import os
import re

def _collect_bug_keys(problems: list[dict]) -> dict[str, list[str]]:
    bug_keys: dict[str, set[str]] = {}
    for problem in problems:
        rel = problem.get('file', '')
        key = _BUG_KEY_MAP.get(problem.get('type', ''))
        if rel and key:
            bug_keys.setdefault(rel, set()).add(key)
    return {rel: _ordered_bug_keys(keys) for rel, keys in bug_keys.items()}


def _ordered_bug_keys(keys) -> list[str]:
    unique = {str(key).lower() for key in keys if key}
    ordered = [key for key in _BUG_KEY_ORDER if key in unique]
    ordered.extend(sorted(key for key in unique if key not in _BUG_KEY_ORDER))
    return ordered


def _mint_bug_entity(file_name: str, bug_key: str) -> str:
    pool = _BUG_ENTITY_POOL.get(bug_key, ('Bug Imp',))
    seed = sum(ord(ch) for ch in f'{file_name}:{bug_key}')
    title = pool[seed % len(pool)]
    stem = re.sub(r'[^a-z0-9]+', '', file_name.lower())[:8] or 'host'
    return f'{title} of {stem}'


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
