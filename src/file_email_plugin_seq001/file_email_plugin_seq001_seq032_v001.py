"""file_email_plugin_seq001_seq032_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq023_v001 import _failed_checks
from .file_email_plugin_seq001_seq023_v001 import _passed_checks
from .file_email_plugin_seq001_seq033_v001 import _context_10q
from .file_email_plugin_seq001_seq044_v001 import _render_context_request
from .file_email_plugin_seq001_seq051_v001 import _rel
from .file_email_plugin_seq001_seq052_v001 import _append_jsonl
from .file_email_plugin_seq001_seq052_v001 import _write_json
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _write_context_request(
    root: Path,
    config: dict[str, Any],
    record: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    request_id = "ctx-" + hashlib.sha256(
        f"{record['id']}|{record.get('file')}|{record.get('intent_key')}".encode("utf-8")
    ).hexdigest()[:14]
    request = {
        "schema": "context_request/v1",
        "ts": record.get("ts"),
        "request_id": request_id,
        "status": "open",
        "source_email_id": record.get("id"),
        "file": record.get("file"),
        "trigger": record.get("trigger"),
        "intent_key": record.get("intent_key", ""),
        "target_state": record.get("target_state", ""),
        "deepseek_completion_job_id": record.get("deepseek_completion_job_id", ""),
        "operator_state": record.get("operator_state", {}),
        "operator_response_policy": record.get("operator_response_policy", {}),
        "required_context": record.get("context_injection", []),
        "validation_plan": record.get("validation_plan", []),
        "beef_with": record.get("beef_with", ""),
        "ten_q": record.get("ten_q", {}),
        "computed_checks": (record.get("ten_q") or {}).get("checks", []),
        "failed_checks": _failed_checks(record),
        "passed_checks": _passed_checks(record),
        "orchestrator_email_guard": record.get("orchestrator_email_guard", {}),
        "questions": _context_10q(record, event),
        "fulfillment": {
            "store_jsonl": "logs/context_request_fulfillments.jsonl",
            "store_markdown_dir": "logs/context_requests",
            "expected_record": {
                "request_id": request_id,
                "status": "fulfilled",
                "answer": "operator/codex/linkrouter supplied context",
                "files": record.get("context_injection", []),
            },
        },
    }
    req_dir = root / str(config.get("context_request_dir") or "logs/context_requests")
    req_dir.mkdir(parents=True, exist_ok=True)
    json_path = req_dir / f"{request_id}.json"
    md_path = req_dir / f"{request_id}.md"
    _write_json(json_path, request)
    md_path.write_text(_render_context_request(request), encoding="utf-8")
    _write_json(root / "logs" / "context_request_latest.json", request)
    _append_jsonl(root / "logs" / "context_requests.jsonl", request)
    return {
        "request_id": request_id,
        "status": "open",
        "ten_q": request.get("ten_q", {}),
        "computed_checks": request.get("computed_checks", []),
        "orchestrator_email_guard": request.get("orchestrator_email_guard", {}),
        "questions": request["questions"],
        "paths": {
            "json": _rel(root, json_path),
            "markdown": _rel(root, md_path),
            "latest": "logs/context_request_latest.json",
            "history": "logs/context_requests.jsonl",
            "fulfillments": "logs/context_request_fulfillments.jsonl",
        },
    }
