"""codex_compat_state_from_deletions_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _state_from_deletions(deletion_ratio: float, hesitation_count: int = 0) -> str:
    if deletion_ratio > 0.4 or hesitation_count > 5:
        return "frustrated"
    if deletion_ratio > 0.2 or hesitation_count > 2:
        return "hesitant"
    if deletion_ratio > 0:
        return "neutral"
    return "unknown"
