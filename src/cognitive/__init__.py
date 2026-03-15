"""cognitive/ — Cognitive state detection and agent behavior adaptation.

Maps keystroke telemetry signals into actionable intelligence:
  - Classify operator cognitive state (7 states)
  - Adapt agent behavior via prompt injection
  - Detect unsaid thoughts from deleted content
  - Track drift across sessions
"""
from src.cognitive.adapter_seq001_v001 import get_cognitive_modifier, VALID_STATES
from src.cognitive.unsaid_seq002_v001 import extract_unsaid_thoughts
from src.cognitive.drift_seq003_v001 import detect_session_drift, build_cognitive_context

__all__ = [
    "get_cognitive_modifier",
    "VALID_STATES",
    "extract_unsaid_thoughts",
    "detect_session_drift",
    "build_cognitive_context",
]
