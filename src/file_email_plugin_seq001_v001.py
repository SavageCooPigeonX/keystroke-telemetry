"""Pigeon compliance facade for src/file_email_plugin_seq001_v001.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "src").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(__name__, globals(), 'src/file_email_plugin_seq001_v001.py')

from src.file_email_text_chain_seq001_v001 import (
    render_text_chain_file_email,
    render_text_chain_learning_digest,
    set_text_chain_root,
    text_chain_subject,
)
import os
import json

_legacy_emit_file_email = emit_file_email
_legacy_emit_learning_digest_email = emit_learning_digest_email
render_file_email = render_text_chain_file_email
render_learning_digest_email = render_text_chain_learning_digest
_subject = text_chain_subject
_legacy_email_delivery_status = email_delivery_status
_legacy_deliver_resend = _deliver_resend


def mail_quality_gate(body, record=None):
    """Return whether visible mail has enough human signal to deserve delivery."""
    text = str(body or "")
    lowered = text.lower()
    required = {
        "learned": "i learned:" in lowered,
        "did": "i did:" in lowered,
        "next": "next i am planning:" in lowered,
        "need": "i need from you:" in lowered or "text back like a message:" in lowered,
        "context": "context" in lowered or "hot files" in lowered or "woke files" in lowered,
        "why": "because" in lowered or "reason" in lowered or "i heard" in lowered,
    }
    missing = [key for key, ok in required.items() if not ok]
    return {
        "schema": "file_mail_quality_gate/v1",
        "passed": not missing,
        "missing": missing,
        "event_type": (record or {}).get("event_type", ""),
        "file": (record or {}).get("file", ""),
    }


def _deliver_resend(root, config, record, body):
    quality = mail_quality_gate(body, record)
    _write_quality_status(root, quality)
    if not quality["passed"]:
        return {"status": "blocked_by_mail_quality_gate", "mode": config.get("delivery_mode"), "quality": quality}
    mode = os.environ.get("FILE_EMAIL_DELIVERY") or str((config or {}).get("delivery_mode") or "resend_dry_run")
    if mode == "resend" and str((record or {}).get("event_type")) == "codex_prompt" and not _urgent_prompt_receipt(record):
        return {
            "status": "digest_deferred",
            "mode": mode,
            "quality": quality,
            "reason": "codex prompt receipts default to digest unless urgency is high",
        }
    return _legacy_deliver_resend(root, config, record, body)


def emit_file_email(root, event, config=None):
    set_text_chain_root(root)
    try:
        return _legacy_emit_file_email(root, event, config=config)
    finally:
        set_text_chain_root(None)


def emit_learning_digest_email(root, learning_result, config=None):
    set_text_chain_root(root)
    try:
        return _legacy_emit_learning_digest_email(root, learning_result, config=config)
    finally:
        set_text_chain_root(None)


def email_delivery_status(root, config=None):
    keys = ("RESEND_API_KEY", "RESEND_FROM", "FILE_EMAIL_DELIVERY", "RESEND_USER_AGENT")
    before = {key: os.environ.get(key) for key in keys}
    try:
        return _legacy_email_delivery_status(root, config=config)
    finally:
        for key, value in before.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _urgent_prompt_receipt(record):
    operator = record.get("operator_state") if isinstance(record, dict) and isinstance(record.get("operator_state"), dict) else {}
    text = " ".join([
        str(record.get("reason", "")) if isinstance(record, dict) else "",
        str(operator.get("latest_operator_text", "")),
        str(operator.get("primary_operator_intent", "")),
    ]).lower()
    return any(word in text for word in ("urgent", "important", "frustrated", "wtf", "blocked", "broken"))


def _write_quality_status(root, quality):
    try:
        path = Path(root) / "logs" / "file_email_quality_latest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(quality, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass

if __name__ == "__main__":
    _entry = globals().get("main") or globals().get("_main")
    raise SystemExit(_entry() if callable(_entry) else 0)
