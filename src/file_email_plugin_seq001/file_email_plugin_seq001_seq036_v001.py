"""file_email_plugin_seq001_seq036_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq023_v001 import _failed_checks
from .file_email_plugin_seq001_seq038_v001 import _file_memory_tags
from typing import Any
import hashlib
import re

def _file_memory_thread_id(file_path: str) -> str:
    return "fmt-" + hashlib.sha256(str(file_path or "unknown").replace("\\", "/").encode("utf-8")).hexdigest()[:14]


def _file_memory_message(
    record: dict[str, Any],
    body: str,
    paths: dict[str, str],
    direction: str,
) -> dict[str, Any]:
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    return {
        "schema": "file_mail_message/v1",
        "ts": record.get("ts"),
        "direction": direction,
        "message_id": record.get("id"),
        "file": record.get("file"),
        "subject": record.get("subject"),
        "body": body,
        "body_preview": re.sub(r"\s+", " ", str(body or "")).strip()[:700],
        "paths": paths,
        "event_type": record.get("event_type"),
        "trigger": record.get("trigger"),
        "intent_key": record.get("intent_key", ""),
        "operator_intent": operator.get("primary_operator_intent", ""),
        "current_work": operator.get("current_work", ""),
        "latest_operator_text": operator.get("latest_operator_text", ""),
        "context_request_id": (record.get("context_request") or {}).get("request_id", ""),
        "context_files": record.get("context_injection", []),
        "validation_plan": record.get("validation_plan", []),
        "failed_checks": _failed_checks(record),
        "relationship_tension": record.get("beef_with", ""),
        "tags": _file_memory_tags(record),
    }
