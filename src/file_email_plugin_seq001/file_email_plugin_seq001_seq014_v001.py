"""file_email_plugin_seq001_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq001_v001 import load_file_email_config
from .file_email_plugin_seq001_seq001_v001 import merge_file_email_config
from .file_email_plugin_seq001_seq015_v001 import render_file_email
from .file_email_plugin_seq001_seq017_v001 import _response_policy_snapshot
from .file_email_plugin_seq001_seq032_v001 import _write_context_request
from .file_email_plugin_seq001_seq034_v001 import _file_mail_memory_hint
from .file_email_plugin_seq001_seq035_v001 import _write_file_mail_memory
from .file_email_plugin_seq001_seq041_v001 import _operator_state_snapshot
from .file_email_plugin_seq001_seq047_v001 import _deliver_resend
from .file_email_plugin_seq001_seq049_v001 import _write_outbox
from .file_email_plugin_seq001_seq050_v001 import _subject
from .file_email_plugin_seq001_seq051_v001 import _safe_mailbox
from .file_email_plugin_seq001_seq052_v001 import SCHEMA
from .file_email_plugin_seq001_seq052_v001 import _append_jsonl
from datetime import datetime, timezone
from pathlib import Path
from src.deepseek_receipt_resolver_seq001_v001 import resolve_deepseek_receipt
from typing import Any
import hashlib
import json
import re

def emit_file_email(root: Path, event: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    now = datetime.now(timezone.utc)
    file_path = str(event.get("file") or "unknown")
    beef_with = str(event.get("beef_with") or "the last file that touched global state")
    digest = hashlib.sha256(json.dumps(event, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    record = {
        "schema": SCHEMA,
        "ts": now.isoformat(),
        "id": f"file-email:{digest}",
        "trigger": event.get("trigger", "manual"),
        "event_type": event.get("event_type", "touch"),
        "file": file_path,
        "from": f"{_safe_mailbox(Path(file_path).stem)}@{config.get('sender_domain', 'files.local')}",
        "to": config.get("recipient", "operator@local"),
        "subject": _subject(file_path, beef_with, event),
        "beef_with": beef_with,
        "intent_key": event.get("intent_key", ""),
        "target_state": event.get("target_state", ""),
        "decision": event.get("decision", ""),
        "interlink_score": event.get("interlink_score", 0),
        "reason": event.get("reason", ""),
        "file_comment": event.get("file_comment", ""),
        "deepseek_completion_job_id": event.get("deepseek_completion_job_id", ""),
        "context_injection": event.get("context_injection", []),
        "validation_plan": event.get("validation_plan", []),
        "ten_q": event.get("ten_q", {}),
        "orchestrator_email_guard": event.get("orchestrator_email_guard", {}),
    }
    record["deepseek_receipt"] = resolve_deepseek_receipt(root, record["deepseek_completion_job_id"], file_path)
    record["operator_state"] = _operator_state_snapshot(root, event)
    record["operator_response_policy"] = _response_policy_snapshot(root, event, surface="file_mail")
    record["mail_memory"] = _file_mail_memory_hint(root, config, record)
    record["context_request"] = _write_context_request(root, config, record, event)
    body = render_file_email(record)
    paths = _write_outbox(root, config, record, body, now)
    record["paths"] = paths
    record["mail_memory"] = _write_file_mail_memory(root, config, record, body, paths)
    record["resend"] = _deliver_resend(root, config, record, body)
    _append_jsonl(root / "logs" / "file_email_outbox.jsonl", record)
    return record
