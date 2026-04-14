"""_resolve_flow_import_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 35 lines | ~303 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import importlib
import re

def flow_import(seq_prefix: str, *attrs: str, search_dir: Path | None = None) -> Any:
    """Import a flow module by seq prefix, optionally extracting attributes.

    Args:
        seq_prefix: e.g. "backward_seq007", "flow_engine_seq003"
        *attrs: attribute names to extract. If one attr, returns it directly.
                If multiple, returns tuple. If none, returns the module.
        search_dir: override search directory (default: pigeon_brain/flow/)

    Returns:
        module, single attribute, or tuple of attributes.
    """
    mod_name = _find_module(seq_prefix, search_dir)
    if mod_name is None:
        raise ImportError(
            f"No pigeon module matching '{seq_prefix}' found in "
            f"{search_dir or _FLOW_DIR}"
        )

    # Build the full dotted import path
    pkg = "pigeon_brain.flow"
    full = f"{pkg}.{mod_name}"
    mod = importlib.import_module(full)

    if not attrs:
        return mod
    if len(attrs) == 1:
        return getattr(mod, attrs[0])
    return tuple(getattr(mod, a) for a in attrs)
