"""file_email_plugin_seq001_seq048_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq051_v001 import _safe_tag
from .file_email_plugin_seq001_seq052_v001 import DEFAULT_CONFIG
from pathlib import Path
from src.local_env_loader_seq001_v001 import load_local_env
from typing import Any
import html
import os
import re

def _load_local_email_env(root: Path) -> dict[str, bool]:
    loaded = load_local_env(
        root,
        keys={"RESEND_API_KEY", "RESEND_FROM", "FILE_EMAIL_DELIVERY", "RESEND_USER_AGENT"},
    )
    return {key: True for key in loaded}


def _resend_payload(config: dict[str, Any], record: dict[str, Any], body: str) -> dict[str, Any]:
    text = body
    return {
        "from": os.environ.get("RESEND_FROM") or str(config.get("resend_from") or DEFAULT_CONFIG["resend_from"]),
        "to": [record.get("to") or DEFAULT_CONFIG["recipient"]],
        "subject": record.get("subject") or "File comedy dispatch",
        "text": text,
        "html": "<pre style=\"white-space:pre-wrap;font-family:monospace\">" + html.escape(text) + "</pre>",
        "headers": {
            "X-File-Email-Id": str(record.get("id", "")),
            "X-Context-Request-Id": str((record.get("context_request") or {}).get("request_id", "")),
            "X-Intent-Key": str(record.get("intent_key", ""))[:240],
            "X-10Q-Score": str((record.get("ten_q") or {}).get("score", "")),
            "X-10Q-Passed": str((record.get("ten_q") or {}).get("passed", "")),
            "X-Orchestrator-Email-Guard": str((record.get("orchestrator_email_guard") or {}).get("decision", "")),
        },
        "tags": [
            {"name": "trigger", "value": _safe_tag(record.get("trigger", "manual"))},
            {"name": "event_type", "value": _safe_tag(record.get("event_type", "touch"))},
        ],
    }
