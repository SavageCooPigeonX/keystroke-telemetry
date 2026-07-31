"""Compatibility facade for the split perpendicular DeepSeek lane."""

from .file_sim_deepseek_lane_seq001_v001_compiled import (
    CONTEXT_PACK,
    PROMPT_JOBS,
    queue_perpendicular_deepseek_job,
)

__all__ = ["CONTEXT_PACK", "PROMPT_JOBS", "queue_perpendicular_deepseek_job"]
