"""_resolve_pb_import_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 18 lines | ~161 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from typing import Any
import importlib
import re

def pb_import(seq_prefix: str, *attrs: str) -> Any:
    """Import from pigeon_brain/ root (not flow/)."""
    pb_dir = _FLOW_DIR.parent
    mod_name = _find_module(seq_prefix, pb_dir)
    if mod_name is None:
        raise ImportError(f"No pigeon module matching '{seq_prefix}' in {pb_dir}")
    full = f"pigeon_brain.{mod_name}"
    mod = importlib.import_module(full)
    if not attrs:
        return mod
    if len(attrs) == 1:
        return getattr(mod, attrs[0])
    return tuple(getattr(mod, a) for a in attrs)
