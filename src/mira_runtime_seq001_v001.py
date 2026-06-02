"""Public MIRA runtime facade.

MIRA is the codebase/Opus-side Memory Intent Reconstruction Agent:
Map -> Infer -> Reconstruct -> Align.

The implementation currently lives in the legacy hush_intent_runtime module for
compatibility with existing imports; new code should import from this facade.
"""
from __future__ import annotations

from src.hush_intent_runtime_seq001_v001 import (
    build_hush_intent_runtime,
    build_mira_runtime,
    classify_active_repo,
    render_hush_intent_runtime,
    render_mira_runtime,
)

__all__ = [
    "build_mira_runtime",
    "render_mira_runtime",
    "classify_active_repo",
    "build_hush_intent_runtime",
    "render_hush_intent_runtime",
]
