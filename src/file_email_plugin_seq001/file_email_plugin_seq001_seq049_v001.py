"""file_email_plugin_seq001_seq049_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq051_v001 import _rel
from .file_email_plugin_seq001_seq051_v001 import _safe_filename
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path
from typing import Any
import os
import re

def _write_outbox(
    root: Path,
    config: dict[str, Any],
    record: dict[str, Any],
    body: str,
    now: datetime,
) -> dict[str, str]:
    outbox = root / str(config.get("outbox_dir") or "logs/file_email_outbox")
    outbox.mkdir(parents=True, exist_ok=True)
    safe = _safe_filename(f"{now.strftime('%Y%m%dT%H%M%S')}_{Path(record['file']).stem}_{record['event_type']}")
    paths: dict[str, str] = {}
    if config.get("write_markdown", True):
        md_path = outbox / f"{safe}.md"
        md_path.write_text(body, encoding="utf-8")
        (root / "logs" / "file_email_latest.md").write_text(body, encoding="utf-8")
        paths["markdown"] = _rel(root, md_path)
    if config.get("write_eml", True):
        msg = EmailMessage()
        msg["From"] = record["from"]
        msg["To"] = record["to"]
        msg["Subject"] = record["subject"]
        msg["Date"] = format_datetime(now)
        msg["Message-ID"] = make_msgid(domain=str(config.get("sender_domain", "files.local")))
        msg.set_content(body, subtype="plain", charset="utf-8")
        eml_path = outbox / f"{safe}.eml"
        eml_path.write_bytes(bytes(msg))
        paths["eml"] = _rel(root, eml_path)
    return paths


def _choose_beef(proposal: dict[str, Any], proposals: list[dict[str, Any]]) -> str:
    refs = proposal.get("context_injection") if isinstance(proposal.get("context_injection"), list) else []
    self_path = str(proposal.get("path") or "")
    for item in refs:
        item_s = str(item)
        if item_s and item_s != self_path and not item_s.lower().endswith("manifest.md"):
            return item_s
    for other in proposals:
        other_path = str(other.get("path") or "")
        if other_path and other_path != self_path:
            return other_path
    return "unresolved shared state"
