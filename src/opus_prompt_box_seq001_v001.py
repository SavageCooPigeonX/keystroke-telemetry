"""Compatibility facade for the split Opus prompt box."""

from .opus_prompt_box_seq001_v001_compiled import (
    CANDIDATES_LOG,
    DONE_STATUSES,
    DROP_STATUS,
    HISTORY_JSONL,
    LATEST_JSON,
    LATEST_MD,
    MAX_OPEN_PROBLEMS,
    OPEN_STATUSES,
    SCHEMA,
    TAX_HALF_LIFE_HOURS,
    queue_prompt_box_candidate,
    refine_opus_prompt_box,
    render_opus_prompt_box,
)

__all__ = [
    "CANDIDATES_LOG",
    "DONE_STATUSES",
    "DROP_STATUS",
    "HISTORY_JSONL",
    "LATEST_JSON",
    "LATEST_MD",
    "MAX_OPEN_PROBLEMS",
    "OPEN_STATUSES",
    "SCHEMA",
    "TAX_HALF_LIFE_HOURS",
    "queue_prompt_box_candidate",
    "refine_opus_prompt_box",
    "render_opus_prompt_box",
]
