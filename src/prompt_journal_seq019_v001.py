"""Compatibility wrapper for the stable prompt_journal import path."""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-22T05:36:37.5560367Z
# EDIT_HASH: auto
# EDIT_WHY:  restore journal alias
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import w_pj_s019_v001 as _compat


def __getattr__(name: str) -> Any:
    return getattr(_compat, name)


def log_enriched_entry(
    root: Path,
    msg: str,
    files_open: list[str],
    session_n: int,
) -> dict[str, Any]:
    return _compat.log_enriched_entry(root, msg, files_open, session_n)


__all__ = ['log_enriched_entry']