"""u_pj_s019_v002_d0402_λC_composition_utils_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _composition_key(comp: dict) -> str:
    parts = [
        str(comp.get('event_hash', '')),
        str(comp.get('first_key_ts', '')),
        str(comp.get('last_key_ts', '')),
        str(comp.get('ts', '')),
        str(comp.get('total_keystrokes', '')),
        str(comp.get('duration_ms', '')),
        str(comp.get('final_text', ''))[:120],
    ]
    return '|'.join(parts)


def _recent_bound_composition_keys(root: Path, limit: int = 8) -> set[str]:
    entries = _read_jsonl(root / JOURNAL_PATH)
    keys = set()
    for entry in entries[-limit:]:
        binding = entry.get('composition_binding', {})
        key = binding.get('key')
        if key:
            keys.add(key)
    return keys


def _recent_bound_session_ns(root: Path, limit: int = 8) -> set[int]:
    """Return session_n values already used for composition binding."""
    entries = _read_jsonl(root / JOURNAL_PATH)
    ns: set[int] = set()
    for entry in entries[-limit:]:
        sn = entry.get('session_n')
        if sn is not None:
            ns.add(sn)
    return ns
