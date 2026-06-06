"""file_email_plugin_seq001_seq047_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq010_v001 import email_delivery_status
from .file_email_plugin_seq001_seq046_v001 import _delivery_guard
from .file_email_plugin_seq001_seq048_v001 import _load_local_email_env
from .file_email_plugin_seq001_seq048_v001 import _resend_payload
from .file_email_plugin_seq001_seq052_v001 import DEFAULT_CONFIG
from .file_email_plugin_seq001_seq052_v001 import _append_jsonl
from .file_email_plugin_seq001_seq052_v001 import _write_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re
import urllib.error
import urllib.request

def _deliver_resend(root: Path, config: dict[str, Any], record: dict[str, Any], body: str) -> dict[str, Any]:
    _load_local_email_env(root)
    configured_mode = str(config.get("delivery_mode") or "resend_dry_run")
    mode = configured_mode if configured_mode == "resend_dry_run" else os.environ.get("FILE_EMAIL_DELIVERY") or configured_mode
    payload = _resend_payload(config, record, body)
    guard = _delivery_guard(record)
    payload_record = {
        "schema": "resend_payload/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "email_id": record.get("id"),
        "api_url": config.get("resend_api_url"),
        "api_key_present": bool(os.environ.get("RESEND_API_KEY")),
        "orchestrator_guard": guard,
        "payload": payload,
    }
    _write_json(root / "logs" / "resend_payload_latest.json", payload_record)
    _append_jsonl(root / "logs" / "resend_payloads.jsonl", payload_record)
    if mode != "resend":
        email_delivery_status(root, config)
        return {
            "status": "dry_run",
            "mode": mode,
            "would_send": bool(guard.get("aligned")),
            "orchestrator_guard": guard,
            "payload_path": "logs/resend_payload_latest.json",
        }
    if not guard.get("aligned"):
        email_delivery_status(root, config)
        return {
            "status": "blocked_by_orchestrator",
            "mode": mode,
            "reason": guard.get("reason", "consensus guard failed"),
            "orchestrator_guard": guard,
            "payload_path": "logs/resend_payload_latest.json",
        }
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        email_delivery_status(root, config)
        return {
            "status": "not_sent",
            "mode": mode,
            "reason": "missing_RESEND_API_KEY",
            "payload_path": "logs/resend_payload_latest.json",
        }
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            str(config.get("resend_api_url") or DEFAULT_CONFIG["resend_api_url"]),
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": os.environ.get("RESEND_USER_AGENT") or str(config.get("resend_user_agent") or DEFAULT_CONFIG["resend_user_agent"]),
                "Idempotency-Key": str(record.get("id", ""))[:64],
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        parsed = json.loads(text) if text.strip().startswith("{") else {"raw": text}
        email_delivery_status(root, config)
        return {"status": "sent", "mode": mode, "response": parsed}
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        email_delivery_status(root, config)
        return {"status": "error", "mode": mode, "http_status": exc.code, "error": body_text[:1000]}
    except Exception as exc:
        email_delivery_status(root, config)
        return {"status": "error", "mode": mode, "error": str(exc)}
