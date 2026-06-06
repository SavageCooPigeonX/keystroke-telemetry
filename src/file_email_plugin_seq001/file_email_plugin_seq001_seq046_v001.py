"""file_email_plugin_seq001_seq046_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _delivery_guard(record: dict[str, Any]) -> dict[str, Any]:
    ten_q = record.get("ten_q") or {}
    guard = record.get("orchestrator_email_guard") or {}
    if record.get("event_type") == "learning_digest" and (guard.get("decision") == "allow_email" or guard.get("aligned")):
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "reason": guard.get("reason", "slow self-fix learning digest is operator-visible"),
        }
    if record.get("file") == "orchestrator/prompt_monitor" and record.get("trigger") in {"log_prompt", "pre_prompt", "os_hook_auto", "composition", "composition_submit"}:
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "reason": "file sim prompt monitor receipt is operator-visible even without a safe rewrite candidate",
        }
    if not ten_q or not guard:
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": False,
            "decision": "local_only",
            "reason": "no consensus 10Q guard attached",
        }
    if not ten_q.get("passed"):
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": False,
            "decision": "local_only",
            "reason": f"10Q failed: {ten_q.get('reason', 'unknown')}",
        }
    if guard.get("decision") != "allow_email" or not guard.get("aligned"):
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": False,
            "decision": guard.get("decision", "local_only"),
            "reason": guard.get("reason", "orchestrator did not allow email"),
        }
    return {
        "schema": "email_delivery_guard/v1",
        "aligned": True,
        "decision": "allow_email",
        "reason": guard.get("reason", "10Q consensus passed"),
    }
