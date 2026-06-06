"""file_email_plugin_seq001_seq025_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq028_v001 import _plain_snip
from pathlib import Path
from typing import Any
import os
import re

def _done_lines(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
) -> list[str]:
    lines = [
        f"Stored this as message `{memory.get('message_count', 0)}` in `{memory.get('markdown') or memory.get('path') or 'logs/file_memory'}`.",
        f"Kept the router handle alive: `{(record.get('context_request') or {}).get('request_id', 'none')}`.",
    ]
    reason = _plain_snip(record.get("reason"), 180)
    if reason:
        lines.insert(0, reason)
    deepseek = _deepseek_done_line(record)
    if deepseek:
        lines.insert(1 if reason else 0, deepseek)
    if record.get("event_type") == "completion":
        lines.append("Closed a lifecycle email and checked whether completion had real bound evidence.")
    elif record.get("event_type") == "codex_prompt":
        lines.append("Logged a one-per-Codex-prompt operator receipt on the local dev surface.")
    elif record.get("event_type") == "compile":
        lines.append("Registered why this file was selected for the current context pack.")
    else:
        lines.append(f"Logged `{Path(file_path).name}` as touched in the operator-intent trail.")
    return lines[:5]


def _deepseek_done_line(record: dict[str, Any]) -> str:
    receipt = record.get("deepseek_receipt") if isinstance(record.get("deepseek_receipt"), dict) else {}
    status = str(receipt.get("status") or "")
    if not status or status == "none":
        return ""
    job_id = str(receipt.get("job_id") or record.get("deepseek_completion_job_id") or "")
    summary = _plain_snip(receipt.get("summary"), 160)
    preview = _plain_snip(receipt.get("completion_preview"), 220)
    if preview:
        return f"DeepSeek `{job_id}` {status}: {summary}; returned: {preview}"
    return f"DeepSeek `{job_id}` {status}: {summary}"
