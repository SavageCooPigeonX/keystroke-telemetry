"""Compatibility facade for the split Opus micro-pulse runtime."""

from .opus_micro_pulse_runtime_seq001_v001_compiled import (
    EXECUTOR_PROMPT,
    HISTORY,
    LATEST,
    MARKDOWN,
    PROMPT_CLASSES,
    SCHEMA,
    build_opus_micro_pulse_runtime,
    classify_prompt,
    render_opus_micro_pulse,
)

__all__ = [
    "EXECUTOR_PROMPT",
    "HISTORY",
    "LATEST",
    "MARKDOWN",
    "PROMPT_CLASSES",
    "SCHEMA",
    "build_opus_micro_pulse_runtime",
    "classify_prompt",
    "render_opus_micro_pulse",
]
