"""batch_rewrite_sim_seq001_seq023_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq021_v001 import _render_incompatibilities
from typing import Any
import os
import re

def _deepseek_completion_prompt(result: dict[str, Any], proposal: dict[str, Any]) -> str:
    intent = result.get("intent") or {}
    incompat = _render_incompatibilities(proposal)
    return "\n".join([
        "You are the DeepSeek deep source rewrite path.",
        "Draft a source rewrite plan or patch only for the approved file.",
        f"INTENT_KEY: {intent.get('intent_key', '')}",
        f"TARGET_STATE: {result.get('target_state', 'interlinked_source_state')}",
        f"FILE: {proposal.get('path')}",
        f"PROPOSED_FIX: {proposal.get('proposed_fix')}",
        f"INCOMPATIBILITIES: {incompat}",
        "CONTEXT_FILES:",
        *[f"- {item}" for item in (proposal.get("context_injection") or [])[:10]],
        "VALIDATION:",
        *[f"- {item}" for item in (proposal.get("validation_plan") or [])[:8]],
        "RULE: Do not overwrite until orchestrator approval exists. Copilot executes; validation can veto.",
    ])


def _deepseek_model() -> str:
    return os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro"


def _orchestrator_oath(compiled: dict[str, Any]) -> dict[str, Any]:
    intent_key = compiled.get("intent_key", "")
    lines = [
        "I will compile intent before action.",
        "I will let files testify before they are overwritten.",
        "I will use quick proposal and grading before spending deep rewrite tokens.",
        "I will inject context before execution.",
        "I will explain incompatible file proposals instead of hiding conflicts.",
        "I will let Copilot execute only bounded approved work.",
        "I will let validation veto every rewrite.",
    ]
    return {
        "schema": "orchestrator_dev_oath/v1",
        "intent_key": intent_key,
        "short": "Orchestrator oath: compile intent, hear file testimony, approve narrowly, execute with Copilot, validate before trust.",
        "lines": lines,
    }
