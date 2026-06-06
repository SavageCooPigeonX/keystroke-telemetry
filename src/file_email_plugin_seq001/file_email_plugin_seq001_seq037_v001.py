"""file_email_plugin_seq001_seq037_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq040_v001 import _bump
from typing import Any
import re

def _empty_file_memory_knowledge() -> dict[str, Any]:
    return {
        "operator_intents": {},
        "intent_keys": {},
        "neighbors": {},
        "failed_checks": {},
        "decisions": {},
        "operator_notes": [],
        "preferred_context": [],
        "avoid_rules": [],
        "style_notes": [
            "visible mail should adapt to operator cognitive style",
            "machine structure belongs under the hood",
        ],
        "last_current_work": "",
        "last_operator_signal": "",
    }


def _merge_file_memory_knowledge(knowledge: Any, event: dict[str, Any]) -> dict[str, Any]:
    out = knowledge if isinstance(knowledge, dict) else _empty_file_memory_knowledge()
    for key, default in _empty_file_memory_knowledge().items():
        out.setdefault(key, default.copy() if isinstance(default, (dict, list)) else default)
    _bump(out["operator_intents"], event.get("operator_intent"))
    _bump(out["intent_keys"], event.get("intent_key"))
    _bump(out["decisions"], event.get("event_type"))
    _bump(out["neighbors"], event.get("relationship_tension"))
    for item in event.get("context_files") or []:
        _bump(out["neighbors"], item)
    for item in event.get("failed_checks") or []:
        if isinstance(item, dict):
            _bump(out["failed_checks"], item.get("key"))
    if event.get("current_work"):
        out["last_current_work"] = event.get("current_work")
    if event.get("latest_operator_text"):
        out["last_operator_signal"] = str(event.get("latest_operator_text"))[:500]
    return out
