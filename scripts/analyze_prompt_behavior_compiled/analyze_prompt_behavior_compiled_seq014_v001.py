"""analyze_prompt_behavior_compiled_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
import re

def _next_response_policy(row: PromptRow, correction_modes: list[str], reward_modes: list[str]) -> str:
    modes = set(correction_modes + reward_modes)
    if row.reinforcement in {"negative", "negative_soft", "mixed"}:
        if "guessed_without_trace" in modes or "trace_used_too_late_or_too_shallow" in modes:
            return "open logs first; quote exact sessions; compile intent keys; only then answer."
        if "execution_before_model_alignment" in modes:
            return "pause implementation; restate hidden compiler test; ask or inspect before patching."
        if "frontend_change_erased_intelligence_signal" in modes or "ui_destroyed_signal" in modes:
            return "treat UI as intelligence expression; preserve prior signal hierarchy before visual changes."
        if "generic_chatgpt_voice" in modes:
            return "drop polished summary; use internal-log style with evidence and repair action."
        return "respond as correction intake: identify violated expectation, evidence, and repair move."
    if row.reinforcement == "positive":
        if "execute_verified_work" in modes:
            return "continue with bounded implementation plus verification; keep evidence visible."
        if "caught_hidden_architecture" in modes:
            return "expand architecture and pressure-test the insight before execution."
        return "continue momentum, but preserve exact operator wording and latent model."
    if row.cognitive_load >= 0.55:
        return "do not summarize away; extract residue, contradictions, and candidate intent keys."
    return "answer directly and keep context light."
