# @pigeon: role=package_root | exports=[TelemetryLogger,HesitationAnalyzer,DriftWatcher,cognitive]
from src._resolve import src_import

TelemetryLogger = src_import("logger_seq003", "TelemetryLogger")
HesitationAnalyzer = src_import("resistance_bridge_seq006", "HesitationAnalyzer")
DriftWatcher = src_import("drift_watcher_seq005", "DriftWatcher")
score_context_budget = src_import("context_budget_seq004", "score_context_budget")

# Cognitive layer — typing-pattern intelligence
from src.cognitive import (
    get_cognitive_modifier,
    extract_unsaid_thoughts,
    detect_session_drift,
    build_cognitive_context,
    VALID_STATES,
)

__all__ = [
    "TelemetryLogger",
    "HesitationAnalyzer",
    "DriftWatcher",
    "score_context_budget",
    "get_cognitive_modifier",
    "extract_unsaid_thoughts",
    "detect_session_drift",
    "build_cognitive_context",
    "VALID_STATES",
]
