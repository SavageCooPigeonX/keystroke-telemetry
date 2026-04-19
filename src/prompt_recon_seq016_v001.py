"""Compatibility wrapper for the legacy prompt_recon import path."""
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
from typing import Any, cast


def _load_runtime_module() -> ModuleType:
    root = Path(__file__).resolve().parent
    this_file = Path(__file__).resolve()
    for candidate in sorted(root.glob('u_prc_s016*.py')):
        resolved = candidate.resolve()
        if resolved == this_file:
            continue
        spec = importlib.util.spec_from_file_location(f'_compat_{candidate.stem}', candidate)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'reconstruct_latest'):
            return mod
    raise ImportError('No runtime prompt recon module exports reconstruct_latest')


_RUNTIME = _load_runtime_module()


def __getattr__(name: str) -> Any:
    return getattr(_RUNTIME, name)


def reconstruct_latest(root: Path) -> dict[str, Any] | None:
    return _RUNTIME.reconstruct_latest(root)


def track_copilot_prompt_mutations(root: Path) -> dict[str, Any]:
    tracker = getattr(_RUNTIME, 'track_copilot_prompt_mutations', None)
    if not callable(tracker):
        raise AttributeError(
            'Runtime prompt recon module does not export track_copilot_prompt_mutations'
        )
    return cast(dict[str, Any], tracker(root))


__all__ = ['reconstruct_latest', 'track_copilot_prompt_mutations']
