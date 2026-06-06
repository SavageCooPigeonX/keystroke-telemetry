"""file_email_plugin_seq001_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq017_v001 import _policy_mail_line
from .file_email_plugin_seq001_seq017_v001 import _prefixed
from .file_email_plugin_seq001_seq023_v001 import _actionable_mail_opening
from .file_email_plugin_seq001_seq023_v001 import _failed_checks
from .file_email_plugin_seq001_seq024_v001 import _learned_lines
from .file_email_plugin_seq001_seq025_v001 import _done_lines
from .file_email_plugin_seq001_seq026_v001 import _need_lines
from .file_email_plugin_seq001_seq026_v001 import _planning_lines
from .file_email_plugin_seq001_seq027_v001 import _actionable_comedy_line
from .file_email_plugin_seq001_seq027_v001 import _failed_check_summary
from .file_email_plugin_seq001_seq027_v001 import _first_validation
from pathlib import Path
from typing import Any
import os
import re

def render_file_email(record: dict[str, Any]) -> str:
    file_path = record.get("file", "unknown")
    beef = record.get("beef_with", "unknown")
    file_name = Path(str(file_path)).name
    file_stem = Path(str(file_path)).stem or "file"
    context_targets = [str(item) for item in (record.get("context_injection") or []) if str(item) != str(file_path)]
    text_chain_target = context_targets[0] if context_targets else str(beef)
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    policy = record.get("operator_response_policy") if isinstance(record.get("operator_response_policy"), dict) else {}
    memory = record.get("mail_memory") if isinstance(record.get("mail_memory"), dict) else {}
    failed_checks = _failed_checks(record)
    lines = [
        f"From: {file_path}",
        f"To: Nikita",
        f"Subject: {record.get('subject', '')}",
        "",
        f"{operator.get('operator_name') or 'Nikita'},",
        "",
        f"File room: `{file_path}`",
        "Blank sheet: learning-only; no source overwrite happened.",
        f"{file_stem}: I heard the complaint and turned it into a validation request.",
        f"{file_name}: I have beef with `{text_chain_target}`",
        "Opus: Backward pass solution -> keep the proof path visible before source mutation.",
        f"{file_stem}: Approval -> {'blocked by failed checks' if failed_checks else 'approved by file checks'}",
        "Grader: open",
        "Text back like a message: `remember: ...`, `use: ...`, `avoid: ...`, `style: ...`",
        "",
        _actionable_mail_opening(file_path, record, operator, memory, failed_checks),
        _policy_mail_line(policy),
        "",
        "I learned:",
        *_prefixed(_learned_lines(file_path, record, operator, memory), "- "),
        "",
        "I did:",
        *_prefixed(_done_lines(file_path, record, operator, memory), "- "),
        "",
        "Next I am planning:",
        *_prefixed(_planning_lines(file_path, record, operator, memory, failed_checks), "- "),
        "",
        "I need from you:",
        *_prefixed(_need_lines(file_path, record, memory, failed_checks), "- "),
        "",
        "Tiny bit of file gossip:",
        _actionable_comedy_line(file_path, beef, record, operator, memory, failed_checks),
        "",
        "Memory thread:",
        f"- `{memory.get('markdown') or memory.get('path') or 'logs/file_memory'}`",
        f"- message: `{memory.get('message_count', 0)}`",
        f"- reply syntax: `remember: ...`, `use: ...`, `avoid: ...`, `style: ...`",
        "",
        "Router receipt, because tools still need a handle:",
        f"- operator intent: `{operator.get('primary_operator_intent') or 'unknown'}`",
        f"- intent: `{record.get('intent_key') or operator.get('operator_intent_key') or 'none'}`",
        f"- context request: `{(record.get('context_request') or {}).get('request_id', 'none')}`",
        f"- validation: `{_first_validation(record)}`",
    ]
    if failed_checks:
        lines.append(f"- failed: `{_failed_check_summary(failed_checks)}`")
    else:
        lines.append("- failed checks: none")
    lines.append("")
    return "\n".join(lines)
