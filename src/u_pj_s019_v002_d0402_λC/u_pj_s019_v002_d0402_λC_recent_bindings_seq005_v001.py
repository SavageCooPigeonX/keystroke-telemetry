"""u_pj_s019_v002_d0402_λC_recent_bindings_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

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
