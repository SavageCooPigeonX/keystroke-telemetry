"""Infer prompt state when keystroke telemetry has no useful signal."""
from __future__ import annotations

import re


def infer_prompt_cognitive_state(prompt: str, fallback: str) -> str:
    lower = str(prompt or "").lower()
    frustration_markers = (
        "broken",
        "still not",
        "not going out",
        "doesn't work",
        "does not work",
        "wtf",
    )
    if any(marker in lower for marker in frustration_markers):
        return "frustrated"
    if re.search(r"\b(um+|uh+|hmm+|how do we|not sure|maybe)\b", lower):
        return "hesitant"
    return fallback
