"""Loader for mechanically migrated over-cap Python modules."""
from __future__ import annotations

import sys
from pathlib import Path


def load_legacy_module(current_name: str, target_globals: dict, original_rel: str):
    """Execute an excluded legacy copy while preserving the original import API."""
    root = Path(__file__).resolve().parents[1]
    original = root / original_rel
    legacy = root / "build" / "pigeon_legacy" / original_rel
    package = current_name.rpartition(".")[0]
    before = set(target_globals)
    target_globals["__file__"] = str(original)
    target_globals["__package__"] = package
    source = legacy.read_text(encoding="utf-8", errors="replace")
    exec(compile(source, str(original), "exec"), target_globals)

    names = target_globals.get("__all__")
    if not names:
        names = [
            name for name in target_globals
            if not (name.startswith("__") and name.endswith("__"))
            and name not in before
        ]
    target_globals["__all__"] = list(names)
    return sys.modules.get(current_name)


__all__ = ["load_legacy_module"]
