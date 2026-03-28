"""Dynamic import resolver for pigeon-named modules in src/.

Eliminates hardcoded version/date/description imports that break on every
pigeon rename. Import by seq identifier only — the resolver finds the
actual file at runtime.

Usage:
    from src._resolve import src_import
    TelemetryLogger = src_import("logger_seq003", "TelemetryLogger")
    mod = src_import("drift_watcher_seq005")  # returns module
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

_SRC_DIR = Path(__file__).parent
_CACHE: dict[str, str] = {}


def _find_module(seq_prefix: str) -> str | None:
    """Find the actual module file matching a seq prefix like 'logger_seq003'.
    
    Also handles dotted subpackage prefixes like 'cognitive.adapter_seq001'
    by searching in the appropriate subdirectory.
    """
    if seq_prefix in _CACHE:
        return _CACHE[seq_prefix]

    # Handle dotted subpackage paths: 'cognitive.adapter_seq001' → search src/cognitive/
    if '.' in seq_prefix:
        parts = seq_prefix.rsplit('.', 1)
        sub_dir = _SRC_DIR / parts[0].replace('.', '/')
        leaf = parts[1]
        if sub_dir.is_dir():
            pattern = re.compile(rf"^{re.escape(leaf)}_v\d+", re.IGNORECASE)
            # Check subpackage first
            for child in sub_dir.iterdir():
                if child.is_dir() and pattern.match(child.name):
                    if (child / "__init__.py").exists():
                        result = parts[0] + "." + child.name
                        _CACHE[seq_prefix] = result
                        return result
            # Check file
            for child in sub_dir.iterdir():
                if child.suffix == ".py" and pattern.match(child.stem):
                    result = parts[0] + "." + child.stem
                    _CACHE[seq_prefix] = result
                    return result
        return None

    pattern = re.compile(rf"^{re.escape(seq_prefix)}_v\d+", re.IGNORECASE)

    # Check for subpackage first (directory with __init__.py)
    for child in _SRC_DIR.iterdir():
        if child.is_dir() and pattern.match(child.name):
            if (child / "__init__.py").exists():
                _CACHE[seq_prefix] = child.name
                return child.name

    # Check for single file
    for child in _SRC_DIR.iterdir():
        if child.suffix == ".py" and pattern.match(child.stem):
            _CACHE[seq_prefix] = child.stem
            return child.stem

    return None


def src_import(seq_prefix: str, *attrs: str) -> Any:
    """Import a src module by seq prefix, optionally extracting attributes.

    Returns module, single attribute, or tuple of attributes.
    """
    mod_name = _find_module(seq_prefix)
    if mod_name is None:
        raise ImportError(
            f"No pigeon module matching '{seq_prefix}' found in {_SRC_DIR}"
        )

    full = f"src.{mod_name}"
    mod = importlib.import_module(full)

    if not attrs:
        return mod
    if len(attrs) == 1:
        return getattr(mod, attrs[0])
    return tuple(getattr(mod, a) for a in attrs)
