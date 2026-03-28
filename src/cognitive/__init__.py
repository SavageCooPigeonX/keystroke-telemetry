"""cognitive/ — Cognitive state detection and agent behavior adaptation.

Maps keystroke telemetry signals into actionable intelligence:
  - Classify operator cognitive state (7 states)
  - Adapt agent behavior via prompt injection
  - Detect unsaid thoughts from deleted content
  - Track drift across sessions
"""
from src._resolve import src_import

get_cognitive_modifier, VALID_STATES = src_import("cognitive.adapter_seq001", "get_cognitive_modifier", "VALID_STATES")
extract_unsaid_thoughts = src_import("cognitive.unsaid_seq002", "extract_unsaid_thoughts")
detect_session_drift, build_cognitive_context = src_import("cognitive.drift_seq003", "detect_session_drift", "build_cognitive_context")

__all__ = [
    "get_cognitive_modifier",
    "VALID_STATES",
    "extract_unsaid_thoughts",
    "detect_session_drift",
    "build_cognitive_context",
]
