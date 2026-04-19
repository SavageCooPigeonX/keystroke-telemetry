"""Compatibility wrapper for the legacy prompt_signal import path."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_runtime_module() -> ModuleType:
    root = Path(__file__).resolve().parent
    this_file = Path(__file__).resolve()
    for candidate in sorted(root.glob('u_psg_s026*.py')):
        resolved = candidate.resolve()
        if resolved == this_file:
            continue
        spec = importlib.util.spec_from_file_location(f'_compat_{candidate.stem}', candidate)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'log_raw_signal'):
            return mod
    raise ImportError('No runtime prompt signal module exports log_raw_signal')


_RUNTIME = _load_runtime_module()


def __getattr__(name: str) -> Any:
    return getattr(_RUNTIME, name)


def log_raw_signal(
    root: Path,
    msg: str,
    files_open: list[str],
    session_n: int,
    signals: dict[str, Any],
    deleted_words: list[str],
    rewrites: list[dict[str, Any]],
    composition_binding: dict[str, Any],
) -> dict[str, Any]:
    return _RUNTIME.log_raw_signal(
        root,
        msg,
        files_open,
        session_n,
        signals,
        deleted_words,
        rewrites,
        composition_binding,
    )


def load_raw_signals(root: Path, after_line: int = 0) -> list[dict[str, Any]]:
    return _RUNTIME.load_raw_signals(root, after_line)


def load_latest_raw(root: Path, n: int = 1) -> list[dict[str, Any]]:
    return _RUNTIME.load_latest_raw(root, n)


__all__ = ['log_raw_signal', 'load_raw_signals', 'load_latest_raw']
