"""file_email_plugin_seq001_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq001_v001 import load_file_email_config
from .file_email_plugin_seq001_seq001_v001 import merge_file_email_config
from .file_email_plugin_seq001_seq048_v001 import _load_local_email_env
from .file_email_plugin_seq001_seq051_v001 import _load_json
from .file_email_plugin_seq001_seq052_v001 import DEFAULT_CONFIG
from .file_email_plugin_seq001_seq052_v001 import _write_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re

def email_delivery_status(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root)
    _load_local_email_env(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    latest = _load_json(root / "logs" / "resend_payload_latest.json") or {}
    mode = os.environ.get("FILE_EMAIL_DELIVERY") or str(config.get("delivery_mode") or "resend_dry_run")
    blockers = []
    if mode != "resend":
        blockers.append("delivery_mode_is_not_resend")
    if not os.environ.get("RESEND_API_KEY"):
        blockers.append("missing_RESEND_API_KEY")
    status = {
        "schema": "file_email_delivery_status/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "can_send": mode == "resend" and bool(os.environ.get("RESEND_API_KEY")),
        "api_key_present": bool(os.environ.get("RESEND_API_KEY")),
        "from": os.environ.get("RESEND_FROM") or str(config.get("resend_from") or DEFAULT_CONFIG["resend_from"]),
        "recipient": config.get("recipient") or DEFAULT_CONFIG["recipient"],
        "api_url": config.get("resend_api_url") or DEFAULT_CONFIG["resend_api_url"],
        "user_agent": os.environ.get("RESEND_USER_AGENT") or str(config.get("resend_user_agent") or DEFAULT_CONFIG["resend_user_agent"]),
        "blockers": blockers,
        "latest_payload": {
            "mode": latest.get("mode"),
            "api_key_present": latest.get("api_key_present"),
            "guard_decision": ((latest.get("orchestrator_guard") or {}).get("decision")),
            "email_id": latest.get("email_id"),
            "ts": latest.get("ts"),
        } if isinstance(latest, dict) else {},
        "how_to_enable": [
            "Set FILE_EMAIL_DELIVERY=resend",
            "Set RESEND_API_KEY",
            "Optionally set RESEND_FROM='File Comedy <contact@myaifingerprint.com>'",
        ],
    }
    _write_json(root / "logs" / "file_email_delivery_status.json", status)
    return status
