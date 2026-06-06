"""Public facade for Opus artifact memory."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

from pathlib import Path

from src.opus_artifact_memory_core_seq001_v001 import (
    build_opus_artifact_memory,
    render_opus_artifact_memory,
)

__all__ = ["build_opus_artifact_memory", "render_opus_artifact_memory"]


if __name__ == "__main__":
    build_opus_artifact_memory(Path.cwd())
