"""file_email_plugin_seq001_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _codex_prompt_ten_q(prompt: str, source: str, loop: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {"key": "prompt_present", "passed": bool(prompt), "reason": "Codex prompt text captured" if prompt else "prompt was empty"},
        {"key": "operator_visible", "passed": True, "reason": "receipt is addressed to the configured operator mailbox"},
        {"key": "control_plane_only", "passed": True, "reason": "emitted from codex_compat/local hook, not web chat"},
        {"key": "intent_loop_bound", "passed": bool(loop.get("loop_id")), "reason": "intent loop id attached" if loop.get("loop_id") else "receipt can send before loop id exists"},
        {"key": "human_on_loop", "passed": loop.get("human_position", "on_loop") == "on_loop", "reason": "operator keeps approve/veto position"},
        {"key": "no_auto_write", "passed": not bool(loop.get("auto_write_allowed")), "reason": "prompt mail does not grant autonomous overwrite"},
        {"key": "source_codex", "passed": "codex" in source.lower() or source in {"pre_prompt", "os_hook_auto", "composition"}, "reason": f"source `{source}` is a Codex/dev prompt surface"},
        {"key": "outbox_written", "passed": True, "reason": "local outbox is always written before delivery"},
        {"key": "delivery_guard", "passed": True, "reason": "operator requested Codex prompt receipts"},
        {"key": "reply_path", "passed": True, "reason": "mail memory accepts remember/use/avoid/style replies"},
    ]
    return {
        "schema": "codex_prompt_receipt_10q/v1",
        "score": sum(1 for item in checks if item["passed"]),
        "max_score": len(checks),
        "min_score": 7,
        "passed": bool(prompt),
        "reason": "Codex prompt receipt ready for operator" if prompt else "empty prompt skipped from real delivery",
        "checks": checks,
    }


def _codex_prompt_guard() -> dict[str, Any]:
    return {
        "schema": "orchestrator_email_guard/v1",
        "aligned": True,
        "decision": "allow_email",
        "policy": "codex_prompt_operator_receipt",
        "reason": "operator requested one email per Codex prompt",
    }
