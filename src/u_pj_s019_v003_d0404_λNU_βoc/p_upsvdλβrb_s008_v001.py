"""u_pj_s019_v003_d0404_λNU_βoc_recent_bindings_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 25 lines | ~205 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .p_u_pj_s001_v001 import JOURNAL_PATH
from .p_u_pj_s002_v001 import _read_jsonl

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
