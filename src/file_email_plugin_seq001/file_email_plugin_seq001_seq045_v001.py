"""file_email_plugin_seq001_seq045_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _ten_q_line(record: dict[str, Any]) -> str:
    ten_q = record.get("ten_q") or {}
    if not ten_q:
        return "unscored"
    status = "PASS" if ten_q.get("passed") else "FAIL"
    return f"{status} {ten_q.get('score', 0)}/{ten_q.get('max_score', 10)} - {ten_q.get('reason', '')}"


def _guard_line(record: dict[str, Any]) -> str:
    guard = record.get("orchestrator_email_guard") or {}
    if not guard:
        return "local_only - no orchestrator guard attached"
    return f"{guard.get('decision', 'unknown')} - {guard.get('reason', '')}"
