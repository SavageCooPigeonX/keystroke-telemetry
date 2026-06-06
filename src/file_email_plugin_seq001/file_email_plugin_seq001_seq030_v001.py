"""file_email_plugin_seq001_seq030_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import os
import re

def _file_role_for_operator(file_path: str, record: dict[str, Any], operator: dict[str, Any]) -> str:
    event_type = record.get("event_type")
    if event_type == "submission":
        return "turn the fresh prompt into a visible, approvable work ticket"
    if event_type == "completion":
        return "close the human-to-repo loop and admit exactly what evidence is still missing"
    if event_type == "compile":
        return f"explain why `{Path(file_path).name}` belongs in the current context pack"
    if event_type == "touch":
        return f"explain why `{Path(file_path).name}` changed while preserving the operator intent trail"
    return "keep the operator intent trail coherent"


def _reasoning_operator_read(record: dict[str, Any], operator: dict[str, Any]) -> str:
    bits = []
    if operator.get("primary_operator_intent"):
        bits.append(f"intent={operator['primary_operator_intent']}")
    if operator.get("prompt_density"):
        bits.append("density=active")
    if operator.get("profile_facts"):
        bits.append("profile=loaded")
    if operator.get("file_job_summary"):
        bits.append("file_council=loaded")
    if not bits:
        bits.append("operator model is sparse; use prompt + intent key")
    return ", ".join(bits)


def _next_bounded_move(record: dict[str, Any], failed_checks: list[dict[str, Any]]) -> str:
    if failed_checks:
        first = failed_checks[0]
        return f"resolve `{first.get('key', 'unknown')}` before trusting completion"
    validation = record.get("validation_plan") or []
    if validation:
        return f"run `{validation[0]}` after approval"
    context = record.get("context_injection") or []
    if context:
        return f"load `{context[0]}` and ask for the smallest safe patch"
    return "ask for missing context before rewrite"


def _loyalty_clause(operator: dict[str, Any]) -> str:
    name = operator.get("operator_name") or "Nikita"
    intent = operator.get("primary_operator_intent") or "the operator's actual intent"
    return f"{name}'s `{intent}` beats file ego, stale model guesses, and ornamental telemetry"
