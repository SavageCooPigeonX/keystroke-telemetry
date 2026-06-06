"""file_email_plugin_seq001_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq028_v001 import _plain_snip
from pathlib import Path
from typing import Any
import os
import re

def _response_policy_snapshot(root: Path, event: dict[str, Any], surface: str = "file_mail") -> dict[str, Any]:
    prompt = " ".join(
        str(event.get(key) or "")
        for key in ("prompt", "reason", "intent_key", "target_state")
        if event.get(key)
    ).strip()
    try:
        from src.operator_response_policy_seq001_v001 import build_operator_response_policy
        policy = build_operator_response_policy(
            root,
            prompt=prompt,
            surface=surface,
            context_pack={},
            inject=False,
            write=True,
        )
        return {
            "schema": policy.get("schema"),
            "ts": policy.get("ts"),
            "active_arm": policy.get("active_arm"),
            "operator_read": policy.get("operator_read"),
            "required_sections": policy.get("required_sections", []),
            "intent_moves": policy.get("intent_moves", [])[:5],
            "probe_files": policy.get("probe_files", [])[:8],
            "next_mutation": policy.get("next_mutation", ""),
            "recent_reward": policy.get("recent_reward", {}),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc), "active_arm": "old_friend_file_mail"}


def _policy_mail_line(policy: dict[str, Any]) -> str:
    if not policy:
        return ""
    arm = policy.get("active_arm") or "old_friend_file_mail"
    read = _plain_snip(policy.get("operator_read"), 180)
    if arm == "quiet_checkpoint":
        return f"Response policy: `{arm}`. I am keeping this calm: {read}"
    if arm == "surgical_engineer":
        return f"Response policy: `{arm}`. Action first, proof second: {read}"
    if arm == "chaos_comedy":
        return f"Response policy: `{arm}`. The jokes are on probation until the next mutation has receipts: {read}"
    return f"Response policy: `{arm}`. Operator read first: {read}"


def _prefixed(values: list[str], prefix: str) -> list[str]:
    return [prefix + value for value in values if value]
