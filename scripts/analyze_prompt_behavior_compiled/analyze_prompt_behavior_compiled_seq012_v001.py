"""analyze_prompt_behavior_compiled_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
import re

def _event_type(row: PromptRow) -> str:
    if row.reinforcement == "positive":
        return "reward"
    if row.reinforcement == "negative":
        return "punishment"
    if row.reinforcement == "negative_soft":
        return "correction"
    if row.reinforcement == "mixed":
        return "mixed"
    if row.cognitive_load >= 0.55:
        return "high_load_exploration"
    return "observation"


def _operator_state(row: PromptRow) -> str:
    if row.reinforcement in {"negative", "negative_soft"} and row.cognitive_load >= 0.55:
        return "high_load_correction"
    if row.reinforcement in {"negative", "negative_soft"}:
        return "correction_pressure"
    if row.reinforcement == "positive" and row.cognitive_load >= 0.45:
        return "excited_alignment"
    if row.reinforcement == "positive":
        return "approval_or_momentum"
    if row.cognitive_load >= 0.55:
        return "dense_architecture_generation"
    if "thinking_partner" in row.themes or "intent_key_compiler" in row.themes:
        return "open_architecture_probe"
    return "routine_prompt"
