"""file_email_plugin_seq001_seq041_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq042_v001 import _infer_operator_intent
from .file_email_plugin_seq001_seq042_v001 import _latest_operator_text
from .file_email_plugin_seq001_seq043_v001 import _current_work_summary
from .file_email_plugin_seq001_seq043_v001 import _state_source
from .file_email_plugin_seq001_seq051_v001 import _load_json
from .file_email_plugin_seq001_seq052_v001 import _latest_jsonl
from pathlib import Path
from typing import Any
import json
import re

def _operator_state_snapshot(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    logs = Path(root) / "logs"
    semantic_latest = _load_json(logs / "semantic_profile_latest.json") or {}
    semantic_profile = _load_json(logs / "semantic_profile.json") or {}
    ai_fingerprint = _load_json(logs / "ai_fingerprint.json") or {}
    operator_current = _load_json(logs / "operator_state_current.json") or {}
    intent_latest = _load_json(logs / "intent_key_latest.json") or {}
    prompt_latest = _latest_jsonl(logs / "prompt_journal.jsonl")
    brain_latest = _load_json(logs / "prompt_brain_latest.json") or {}
    council_latest = _load_json(logs / "file_job_council_latest.json") or {}
    facts = _profile_facts(semantic_profile, ai_fingerprint)
    latest_text = _latest_operator_text(semantic_latest, prompt_latest, brain_latest, event)
    semantic_intents = semantic_latest.get("semantic_intents") if isinstance(semantic_latest.get("semantic_intents"), list) else []
    primary = str(semantic_latest.get("semantic_intent") or "")
    if not primary or primary == "unknown":
        primary = _infer_operator_intent(latest_text, semantic_intents, event)
    return {
        "schema": "operator_state_email/v1",
        "operator_name": _operator_name_from_facts(facts),
        "primary_operator_intent": primary,
        "semantic_intents": semantic_intents,
        "operator_intent_key": event.get("intent_key") or intent_latest.get("intent_key") or brain_latest.get("intent_key") or "",
        "current_work": _current_work_summary(latest_text, primary, event, council_latest),
        "latest_operator_text": latest_text,
        "state_source": _state_source(semantic_latest, operator_current, prompt_latest),
        "profile_facts": facts,
        "prompt_density": operator_current.get("prompt_density") if isinstance(operator_current, dict) else {},
        "file_job_summary": council_latest.get("comedy_summary", "") if isinstance(council_latest, dict) else "",
        "numeric_encoding": semantic_latest.get("numeric_encoding", {}) if isinstance(semantic_latest, dict) else {},
    }


def _profile_facts(semantic_profile: dict[str, Any], ai_fingerprint: dict[str, Any]) -> dict[str, Any]:
    semantic_facts = semantic_profile.get("facts") if isinstance(semantic_profile.get("facts"), dict) else {}
    ai_facts = ai_fingerprint.get("facts") if isinstance(ai_fingerprint.get("facts"), dict) else {}
    merged = dict(ai_facts)
    merged.update(semantic_facts)
    return merged


def _operator_name_from_facts(facts: dict[str, Any]) -> str:
    name = facts.get("name") if isinstance(facts.get("name"), dict) else {}
    value = str(name.get("value") or "").strip()
    return value or "Nikita"
