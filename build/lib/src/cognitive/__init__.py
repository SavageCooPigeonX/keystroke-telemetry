"""cognitive/ — Cognitive state detection and agent behavior adaptation.

Maps keystroke telemetry signals into actionable intelligence:
  - Classify operator cognitive state (7 states)
  - Adapt agent behavior via prompt injection
  - Detect unsaid thoughts from deleted content
  - Track drift across sessions
"""
from src.cognitive.adapter_seq001_v002_d0315__cognitive_state_agent_behavior_adapter_lc_verify_pigeon_plugin import get_cognitive_modifier, VALID_STATES
from src.cognitive.unsaid_seq002_v002_d0315__detects_what_operators_meant_but_lc_verify_pigeon_plugin import extract_unsaid_thoughts
from src.cognitive.drift_seq003_v002_d0315__tracks_operator_typing_patterns_across_lc_verify_pigeon_plugin import detect_session_drift, build_cognitive_context

__all__ = [
    "get_cognitive_modifier",
    "VALID_STATES",
    "extract_unsaid_thoughts",
    "detect_session_drift",
    "build_cognitive_context",
]
