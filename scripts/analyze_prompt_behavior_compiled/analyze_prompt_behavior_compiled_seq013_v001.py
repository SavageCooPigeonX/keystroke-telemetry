"""analyze_prompt_behavior_compiled_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
import re

def _infer_trigger(row: PromptRow, previous: list[PromptRow]) -> str:
    prev_themes = Counter(t for item in previous for t in item.themes)
    if row.reinforcement in {"negative", "negative_soft", "mixed"}:
        if "prompt_history_reconstruction" in row.themes or re.search(r"guessed|research|prompt history|logger", row.msg, re.I):
            return "response likely inferred from surface prompt instead of reconstructing from telemetry."
        if "ui_rendering" in row.themes and "entity_intelligence" in row.themes:
            return "response likely treated interface as layout instead of intelligence-surface contract."
        if "intent_key_compiler" in row.themes:
            return "response likely missed intent-key compiler layer or collapsed it into generic planning."
        if prev_themes.get("execution", 0) >= 2:
            return "execution momentum likely outran intent alignment."
        return "operator is correcting an unresolved mismatch between response and latent system model."
    if row.reinforcement == "positive":
        if "execution" in row.themes:
            return "operator is rewarding bounded action or verifiable forward motion."
        if "intent_key_compiler" in row.themes:
            return "operator is rewarding preservation of the hidden compiler architecture."
        if "prompt_history_reconstruction" in row.themes:
            return "operator is rewarding telemetry-grounded reconstruction."
        return "operator is approving current direction or continuing momentum."
    if row.cognitive_load >= 0.55:
        return "operator is producing dense architecture; answer should preserve residue before simplifying."
    return "no strong trigger detected."


def _latent_need(row: PromptRow, correction_modes: list[str], reward_modes: list[str]) -> str:
    modes = set(correction_modes + reward_modes)
    if "guessed_without_trace" in modes or "trace_used_too_late_or_too_shallow" in modes:
        return "needs evidence-first reconstruction from prompt journal and nearby deleted-word residue."
    if "missing_entity_intelligence" in modes:
        return "needs entity/profile/audit intelligence model preserved under any UI or narrative change."
    if "missing_intent_key_layer" in modes:
        return "needs intent keys treated as intermediate representation across humans, files, entities, and audits."
    if "wrong_role_assignment" in modes:
        return "needs agent roles preserved: Codex probe/interface, Claude/Opus orchestrator, DeepSeek compiler/hands, Grok retrieval/probe."
    if "execute_verified_work" in modes:
        return "wants bounded verified work after the latent architecture is understood."
    if "caught_hidden_architecture" in modes:
        return "wants the hidden architecture named, challenged, and connected to prior traces."
    if row.cognitive_load >= 0.55:
        return "needs thought-preserving expansion before task reduction."
    return "needs concise alignment without inventing certainty."
