"""Compatibility wrapper for the legacy prompt_journal import path."""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-02T03:57:02.9061246Z
# EDIT_HASH: auto
# EDIT_WHY:  repair legacy wrapper
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_runtime_module() -> ModuleType:
    root = Path(__file__).resolve().parent
    this_file = Path(__file__).resolve()
    for candidate in sorted(root.glob('u_pj_s019*.py')):
        resolved = candidate.resolve()
        if resolved == this_file:
            continue
        spec = importlib.util.spec_from_file_location(f'_compat_{candidate.stem}', candidate)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'log_enriched_entry'):
            return mod
    raise ImportError('No runtime prompt journal module exports log_enriched_entry')


_RUNTIME = _load_runtime_module()


def __getattr__(name: str) -> Any:
    return getattr(_RUNTIME, name)


def log_enriched_entry(
    root: Path,
    msg: str,
    files_open: list[str],
    session_n: int,
) -> dict[str, Any]:
    return _RUNTIME.log_enriched_entry(root, msg, files_open, session_n)


__all__ = ['log_enriched_entry']
