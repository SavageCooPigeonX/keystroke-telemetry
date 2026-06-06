"""file_self_sim_learning_seq001_seq028_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _deepseek_learning_instruction(
    rel: str,
    intent_model: dict[str, Any],
    node: dict[str, Any],
    validation_plan: list[str],
    readiness: dict[str, Any],
) -> str:
    context_files = [item.get("file") for item in node.get("context_veins", []) if item.get("file")]
    size = node.get("size_pressure") or {}
    split_lines = []
    if size.get("needs_split_plan"):
        split_lines = [
            "SPLIT_PLAN_REQUIRED:",
            f"- current_lines: {size.get('line_count')} state: {size.get('state')} pressure: {size.get('pressure')}",
            "- propose child files plus a facade/wrapper; do not produce a full overwrite",
            "- include reason_not_to_split if tests, imports, or operator memory make extraction unsafe",
        ]
    return "\n".join([
        "You are the deep rewrite planner for one source file.",
        "Do not overwrite source. Produce a plan or patch candidate only.",
        f"INTENT_KEY: {intent_model.get('intent_key', '')}",
        f"FILE: {rel}",
        f"WAKE_ROLE: {node.get('role')}",
        f"RELATIONSHIP_WEIGHT: {node.get('relationship_weight', 0)}",
        f"VALIDATION_CONFIDENCE: {node.get('validation_confidence', 0)}",
        f"READINESS: {readiness.get('state')} - {readiness.get('reason')}",
        *split_lines,
        "LOAD_CONTEXT:",
        *[f"- {item}" for item in context_files[:10]],
        "VALIDATION:",
        *[f"- {item}" for item in validation_plan[:8]],
        "OUTPUT: responsibility diagnosis, minimal rewrite hypothesis, risks, validation command, backward-learning note.",
    ])
