"""file_email_plugin_seq001_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq051_v001 import _load_json
from .file_email_plugin_seq001_seq052_v001 import DEFAULT_CONFIG
from .file_email_plugin_seq001_seq052_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def load_file_email_config(root: Path, write_default: bool = True) -> dict[str, Any]:
    root = Path(root)
    path = root / "logs" / "file_email_config.json"
    raw = _load_json(path) if path.exists() else {}
    migrated = False
    if isinstance(raw, dict):
        if raw.get("recipient") in {"operator@local", "context@myaifingerprint", "context@myaifingerprint.com"}:
            raw["recipient"] = DEFAULT_CONFIG["recipient"]
            migrated = True
        if raw.get("resend_from") in {"File Comedy <onboarding@resend.dev>", "contact@myaifingerprint.com"}:
            raw["resend_from"] = DEFAULT_CONFIG["resend_from"]
            migrated = True
        raw_triggers = raw.get("triggers")
        if isinstance(raw_triggers, list):
            merged_triggers = list(dict.fromkeys([*raw_triggers, "submission", "completion", "learning_digest", "codex_prompt", "hourly_autonomy", "file_opinion", "pipeline_audit"]))
            if merged_triggers != raw_triggers:
                raw["triggers"] = merged_triggers
                migrated = True
    config = merge_file_email_config(raw if isinstance(raw, dict) else {})
    if write_default and (not path.exists() or raw != config or migrated):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, config)
    return config


def merge_file_email_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in (config or {}).items():
        merged[key] = value
    return merged


def mail_quality_gate(text: str) -> dict[str, Any]:
    """Reject status-only file mail that lacks learned/did/next/need signal."""
    lower = str(text or "").lower()
    checks = {
        "learned": bool(re.search(r"\blearned\b|\bi learned\b|what the files learned", lower)),
        "did": bool(re.search(r"\bdid\b|\bi did\b|what got done", lower)),
        "next": bool(re.search(r"\bnext\b|next move|comes next", lower)),
        "need": bool(re.search(r"\bneed\b|i need|needs? from you|missing context", lower)),
    }
    missing = [key for key, passed in checks.items() if not passed]
    return {
        "schema": "file_mail_quality_gate/v1",
        "passed": not missing,
        "checks": checks,
        "missing": missing,
    }
