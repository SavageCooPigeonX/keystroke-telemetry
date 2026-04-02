"""Compatibility wrapper for the legacy copilot prompt manager import path."""

# ── pigeon ────────────────────────────────────
# SEQ: 020 | VER: v003 | 37 lines | ~324 tokens
# DESC:   compatibility_wrapper_for_the_legacy
# INTENT: restore_rename_safe
# LAST:   2026-04-02 @ f8ea95a
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-02T02:53:01.1309614Z
# EDIT_HASH: auto
# EDIT_WHY:  legacy import alias
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_runtime_module():
    root = Path(__file__).resolve().parent
    this_file = Path(__file__).resolve()
    seen: set[Path] = set()
    for pattern in ('管w_cpm_s020*.py', '*_s020*.py'):
        for candidate in sorted(root.glob(pattern)):
            resolved = candidate.resolve()
            if resolved == this_file or resolved in seen:
                continue
            seen.add(resolved)
            spec = importlib.util.spec_from_file_location(f'_compat_{candidate.stem}', candidate)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'refresh_managed_prompt'):
                return mod
    raise ImportError('No runtime prompt manager module exports refresh_managed_prompt')


_RUNTIME = _load_runtime_module()
refresh_managed_prompt = _RUNTIME.refresh_managed_prompt

__all__ = ['refresh_managed_prompt']