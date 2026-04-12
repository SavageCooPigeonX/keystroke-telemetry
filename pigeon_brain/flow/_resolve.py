"""Dynamic import resolver for pigeon-named modules.

Eliminates hardcoded version/date/description imports that break on every
pigeon rename. Import by seq identifier only — the resolver finds the
actual file at runtime.

Usage:
    from ._resolve import flow_import
    run_flow = flow_import("flow_engine_seq003", "run_flow")
    mod = flow_import("backward_seq007")  # returns module
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

_FLOW_DIR = Path(__file__).parent
_CACHE: dict[str, Any] = {}


def _find_module(seq_prefix: str, search_dir: Path | None = None) -> str | None:
    """Find the actual module file matching a seq prefix like 'backward_seq007'.

    Supports both old-style names (backward_seq007_v*.py) and pigeon-style
    names (逆f_ba_s007_v*.py where s007 = seq007).
    """
    if seq_prefix in _CACHE:
        return _CACHE[seq_prefix]

    d = search_dir or _FLOW_DIR
    
    # Extract seq number (e.g., "007" from "backward_seq007")
    seq_match = re.search(r"seq(\d+)$", seq_prefix)
    seq_num = seq_match.group(1) if seq_match else None
    
    # Old-style pattern: backward_seq007_v*
    old_pattern = re.compile(rf"^{re.escape(seq_prefix)}_v\d+", re.IGNORECASE)
    
    # Pigeon-style pattern: *_s007_v* (where 007 is the seq number)
    pigeon_pattern = re.compile(rf"_s0*{seq_num}_v\d+", re.IGNORECASE) if seq_num else None

    # Check for subpackage first (directory with __init__.py)
    for child in d.iterdir():
        if child.is_dir():
            if old_pattern.match(child.name):
                if (child / "__init__.py").exists():
                    _CACHE[seq_prefix] = child.name
                    return child.name
            if pigeon_pattern and pigeon_pattern.search(child.name):
                if (child / "__init__.py").exists():
                    _CACHE[seq_prefix] = child.name
                    return child.name

    # Check for single file
    candidates = []
    for child in d.iterdir():
        if child.suffix == ".py" and child.stem != "__init__" and child.stem != "_resolve":
            if old_pattern.match(child.stem):
                candidates.append(child)
            elif pigeon_pattern and pigeon_pattern.search(child.stem):
                candidates.append(child)
    
    if candidates:
        # Pick newest version
        best = sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        _CACHE[seq_prefix] = best.stem
        return best.stem

    return None


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
