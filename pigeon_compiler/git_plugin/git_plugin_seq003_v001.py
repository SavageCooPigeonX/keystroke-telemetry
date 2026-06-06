"""git_plugin_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .git_plugin_seq002_v001 import _intent_code_numeric
from .git_plugin_seq018_v001 import _BUG_ENTITY_POOL
from .git_plugin_seq018_v001 import _BUG_KEY_MAP
from .git_plugin_seq018_v001 import _BUG_KEY_ORDER
import os
import re

def _intent_code(intent: str) -> str:
    text = (intent or '').lower()
    for needles, code in _INTENT_CODE_RULES:
        if any(needle in text for needle in needles):
            return code
    if not text:
        return 'OT'
    return text[:2].upper()


def _intent_keys_match(intent1: str, intent2: str) -> bool:
    """Check if two intent slugs map to same numeric encoding."""
    return _intent_code_numeric(intent1) == _intent_code_numeric(intent2)


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
