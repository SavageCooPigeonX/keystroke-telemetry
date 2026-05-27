"""Text-chain renderer for file email receipts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.file_email_ambient_state_seq001_v001 import build_email_ambient_state, render_room_chat

_ROOT: Path | None = None


def set_text_chain_root(root: Path | None) -> None:
    global _ROOT
    _ROOT = Path(root) if root is not None else None


def render_text_chain_file_email(record: dict[str, Any]) -> str:
    sender = Path(str(record.get("file") or "unknown")).name
    memory = record.get("mail_memory") if isinstance(record.get("mail_memory"), dict) else {}
    gate = _gate(record)
    ambient = build_email_ambient_state(_ROOT, record)
    lines = _header(record, sender)
    lines.append("Response policy: file_room_text_chain")
    comment = str(record.get("file_comment") or "").strip()
    if comment:
        lines.append(f"My file comment: {comment}")
    lines.extend(render_room_chat(record, ambient, _name(sender), gate))
    if record.get("deepseek_completion_job_id"):
        lines.append(f"DeepSeek {_deepseek_line(record)}")
    lines.extend([
        "",
        "Text back like a message:",
        "`approve` | `revise: ...` | `remember: ...` | `use: ...` | `avoid: ...` | `style: ...`",
        "`remember: ...`, `use: ...`, `avoid: ...`, `style: ...`",
        "Reply `avoid: generic status memo` if this stops feeling like a real file-room text.",
        "",
        "I learned:",
        f"- `{record.get('intent_key') or 'none'}` is the thread key.",
        "I did:",
        f"- opened the file-room conversation for `{record.get('file') or 'unknown'}`.",
        "Next I am planning:",
        f"- {_first(record.get('validation_plan') or ['wait for your reply'])}",
        "I need from you:",
        "- reply with `approve`, `revise: ...`, `use: ...`, or `avoid: ...` so this thread learns a real preference.",
        "",
        "Tiny receipt:",
        "Memory thread:",
        f"- `{memory.get('markdown') or memory.get('path') or 'logs/file_memory'}`",
        f"- state: `{ambient.get('operator_state')}`",
        f"- operator intent: `{_operator_intent(record)}`",
        f"- training pairs: `{ambient.get('training') or 'unknown'}`",
        f"- proposed Opus jobs: `{ambient.get('job_count')}`",
        f"- context request: `{((record.get('context_request') or {}).get('request_id') or 'none')}`",
        f"- validation: `{_first(record.get('validation_plan') or ['none'])}`",
        _failed_line(record),
    ])
    return "\n".join(lines).rstrip() + "\n"


def render_text_chain_learning_digest(record: dict[str, Any]) -> str:
    gate = {"solution": "let files choose pressure from history, then request proof", "approval": "waiting for file packet votes", "decision": "hold until validation"}
    ambient = build_email_ambient_state(_ROOT, record)
    lines = _header(record, "file sim")
    lines.extend(render_room_chat(record, ambient, "file_sim", gate))
    lines.extend([
        "",
        "Text back like a message:",
        "`approve: draft tests` | `revise: ...` | `avoid: stale committee email` | `style: files have grudges`",
        "",
        "I need from you:",
        "- choose approve/revise/avoid/style so the next file-sim digest has a sharper job.",
        "",
        "Memory:",
        f"- `{((record.get('mail_memory') or {}).get('markdown') or 'logs/file_memory')}`",
    ])
    return "\n".join(lines).rstrip() + "\n"


def text_chain_subject(file_path: str, beef_with: str, event: dict[str, Any]) -> str:
    stem = Path(str(file_path or "file")).stem or "file"
    event_type = str(event.get("event_type") or event.get("trigger") or "update")
    if event_type == "hourly_autonomy":
        return f"group text: hourly loop / {stem}"
    if event_type == "codex_prompt":
        return "group text: Opus runtime heard you"
    if event_type in {"compile", "learning_digest"}:
        return f"group text: {stem} has beef"
    return f"group text: {stem} / {event_type}"


def _header(record: dict[str, Any], sender: str) -> list[str]:
    return [f"From: {record.get('from') or sender}", "To: Nikita", f"Subject: {record.get('subject', '')}", ""]


def _gate(record: dict[str, Any]) -> dict[str, str]:
    ten_q = record.get("ten_q") if isinstance(record.get("ten_q"), dict) else {}
    guard = record.get("orchestrator_email_guard") if isinstance(record.get("orchestrator_email_guard"), dict) else {}
    passed = ten_q.get("passed") is True and guard.get("decision") in {"allow_email", "allow", "send", None, ""}
    solution = str(record.get("reason") or "collect context, test plan, then patch artifact")[:260]
    approval = "approved by file checks" if ten_q.get("passed") is True else "not approved yet"
    return {"solution": solution, "approval": approval, "decision": "open" if passed else "hold"}


def _deepseek_line(record: dict[str, Any]) -> str:
    receipt = record.get("deepseek_receipt") if isinstance(record.get("deepseek_receipt"), dict) else {}
    detail = receipt.get("completion_preview") or receipt.get("summary") or receipt.get("completion") or receipt.get("reason") or ""
    return f"`{record.get('deepseek_completion_job_id')}` {receipt.get('status') or 'pending'} {str(detail)[:220]}"


def _failed_line(record: dict[str, Any]) -> str:
    checks = (record.get("ten_q") or {}).get("checks") if isinstance(record.get("ten_q"), dict) else []
    failed = [str(row.get("key") or row.get("name") or row.get("reason") or "check") for row in checks or [] if row.get("passed") is False]
    return f"- failed: `{', '.join(failed[:6])}`" if failed else "- failed checks: none"


def _name(path: str) -> str:
    return Path(str(path or "file")).stem or "file"


def _operator_intent(record: dict[str, Any]) -> str:
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    return str(operator.get("primary_operator_intent") or record.get("intent_key") or "unknown")


def _first(values: list[Any]) -> str:
    return str(values[0]) if values else "none"
