"""file_email_plugin_seq001_seq052_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json
import re

def _latest_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return {}
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            return row
    return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

SCHEMA = "file_email/v1"

DEFAULT_CONFIG = {
    "enabled": True,
    "recipient": "contact@myaifingerprint.com",
    "sender_domain": "files.local",
    "outbox_dir": "logs/file_email_outbox",
    "context_request_dir": "logs/context_requests",
    "memory_dir": "logs/file_memory",
    "per_fire_limit": 6,
    "write_eml": True,
    "write_markdown": True,
    "tone": "adaptive_mail_memory",
    "triggers": ["file_sim", "touch", "compile", "submission", "completion", "learning_digest", "codex_prompt", "hourly_autonomy", "file_opinion", "pipeline_audit"],
    "delivery_mode": "resend_dry_run",
    "resend_api_url": "https://api.resend.com/emails",
    "resend_from": "File Comedy <contact@myaifingerprint.com>",
    "resend_user_agent": "keystroke-telemetry-file-email/1.0",
}
