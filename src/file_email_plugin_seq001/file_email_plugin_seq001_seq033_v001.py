"""file_email_plugin_seq001_seq033_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _context_10q(record: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    file_path = record.get("file", "unknown")
    beef = record.get("beef_with", "unknown")
    checks = {str(item.get("key")): item for item in (record.get("ten_q") or {}).get("checks", [])}
    key_map = {
        "intent": "intent_alignment",
        "ownership": "source_target",
        "required_context": "context_available",
        "beef": "incompatibility_known",
        "incompatibility": "incompatibility_known",
        "deepseek": "deepseek_job_allowed",
        "copilot": "operator_approval",
        "validation": "validation_plan",
        "missing_context": "dirty_state_known",
        "storage": "identity_growth",
    }
    questions = [
        {"n": 1, "key": "intent", "question": f"What exact intent selected `{file_path}`?"},
        {"n": 2, "key": "ownership", "question": "Which manifest or file identity proves this file owns the change?"},
        {"n": 3, "key": "required_context", "question": "Which files must be loaded before rewrite?"},
        {"n": 4, "key": "beef", "question": f"What does `{file_path}` need from `{beef}` before it stops complaining?"},
        {"n": 5, "key": "incompatibility", "question": "Which peer proposal conflicts with this layout or import edge?"},
        {"n": 6, "key": "deepseek", "question": "What should DeepSeek draft, and what must it avoid touching?"},
        {"n": 7, "key": "copilot", "question": "What exact bounded action should Copilot execute?"},
        {"n": 8, "key": "validation", "question": "Which compile/test gates decide whether the rewrite survives?"},
        {"n": 9, "key": "missing_context", "question": "What context is still missing or stale?"},
        {"n": 10, "key": "storage", "question": "Where should the fulfilled context be stored for future prompts?"},
    ]
    for item in questions:
        mapped = key_map.get(str(item.get("key")))
        if mapped and mapped in checks:
            item["computed"] = checks[mapped]
    return questions
