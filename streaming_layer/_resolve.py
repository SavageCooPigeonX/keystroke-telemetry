"""Dynamic import resolver for pigeon-named modules in streaming_layer/.

Usage:
    from streaming_layer._resolve import sl_import
    EventAggregator = sl_import("streaming_layer_aggregator_seq006", "EventAggregator")
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

_SL_DIR = Path(__file__).parent
_CACHE: dict[str, str] = {}


def _find_module(seq_prefix: str) -> str | None:
    if seq_prefix in _CACHE:
        return _CACHE[seq_prefix]

    pattern = re.compile(rf"^{re.escape(seq_prefix)}_v\d+", re.IGNORECASE)

    for child in _SL_DIR.iterdir():
        if child.is_dir() and pattern.match(child.name):
            if (child / "__init__.py").exists():
                _CACHE[seq_prefix] = child.name
                return child.name

    for child in _SL_DIR.iterdir():
        if child.suffix == ".py" and pattern.match(child.stem):
            _CACHE[seq_prefix] = child.stem
            return child.stem

    return None


def sl_import(seq_prefix: str, *attrs: str) -> Any:
    """Import a streaming_layer module by seq prefix, optionally extracting attributes."""
    mod_name = _find_module(seq_prefix)
    if mod_name is None:
        raise ImportError(
            f"No pigeon module matching '{seq_prefix}' found in {_SL_DIR}"
        )

    full = f"streaming_layer.{mod_name}"
    mod = importlib.import_module(full)

    if not attrs:
        return mod
    if len(attrs) == 1:
        return getattr(mod, attrs[0])
    return tuple(getattr(mod, a) for a in attrs)
