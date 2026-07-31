"""Compatibility facade for the split interlinked naming simulator."""

from .file_interlinked_naming_sim_seq001_v001_compiled import (
    HISTORY,
    LATEST,
    MARKDOWN,
    render_interlinked_naming_sim,
    run_interlinked_naming_sim,
    send_naming_grader_email,
)

__all__ = [
    "HISTORY",
    "LATEST",
    "MARKDOWN",
    "render_interlinked_naming_sim",
    "run_interlinked_naming_sim",
    "send_naming_grader_email",
]
