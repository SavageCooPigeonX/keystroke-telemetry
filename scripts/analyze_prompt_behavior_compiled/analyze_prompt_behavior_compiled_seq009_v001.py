"""analyze_prompt_behavior_compiled_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq008_v001 import _mode_matches
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
import re

def _infer_failed_response_style(row: PromptRow, previous: list[PromptRow]) -> list[str]:
    text = row.msg + " " + " ".join(str(x) for x in row.raw.get("deleted_words") or [])
    modes = _mode_matches(text, CORRECTION_MODES)
    prev_themes = Counter(t for item in previous for t in item.themes)
    if "prompt_history_reconstruction" in prev_themes and "guessed_without_trace" not in modes:
        modes.append("trace_used_too_late_or_too_shallow")
    if "execution" in prev_themes and "premature_task_collapse" not in modes and re.search(r"\b(no|wrong|not quite|dont like)\b", text, re.I):
        modes.append("execution_before_model_alignment")
    if "ui_rendering" in prev_themes and "ui_destroyed_signal" not in modes:
        modes.append("frontend_change_erased_intelligence_signal")
    if not modes and row.reinforcement in {"negative", "negative_soft"}:
        modes.append("unspecified_misalignment")
    return modes


def _infer_rewarded_response_style(row: PromptRow, previous: list[PromptRow]) -> list[str]:
    text = row.msg + " " + " ".join(str(x) for x in row.raw.get("deleted_words") or [])
    modes = _mode_matches(text, REWARD_MODES)
    prev_themes = Counter(t for item in previous for t in item.themes)
    if "execution" in prev_themes and "execute_verified_work" not in modes:
        modes.append("bounded_execution_momentum")
    if "prompt_history_reconstruction" in prev_themes and "used_real_logs" not in modes:
        modes.append("trace_grounded_reconstruction")
    if "intent_key_compiler" in prev_themes and "supported_intent_compiler" not in modes:
        modes.append("intent_key_architecture_preserved")
    if not modes and row.reinforcement == "positive":
        modes.append("positive_but_underspecified")
    return modes
