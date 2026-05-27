"""Resolve DeepSeek job receipts for operator mail."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_deepseek_receipt(root: Path, job_id: str, file_path: str = "") -> dict[str, Any]:
    root = Path(root)
    job_id = str(job_id or "")
    receipt = _empty(job_id)
    if not job_id:
        return receipt
    result = _find_result(root, job_id)
    if result:
        return {
            "job_id": job_id,
            "status": "done" if result.get("success") else "failed",
            "model": result.get("model", ""),
            "summary": result.get("reason") or "DeepSeek returned a result",
            "completion_preview": _snip(result.get("completion") or result.get("completion_preview") or ""),
            "source": "logs/deepseek_prompt_results.jsonl",
        }
    queued = _find_queued(root, job_id, file_path)
    if queued:
        return {
            "job_id": job_id,
            "status": queued.get("status", "queued"),
            "model": queued.get("model", ""),
            "summary": queued.get("reason") or queued.get("mode") or "DeepSeek job queued",
            "completion_preview": "",
            "source": queued.get("_source", "logs/deepseek_code_completion_jobs.jsonl"),
        }
    if job_id.startswith("blocked"):
        return {
            "job_id": job_id,
            "status": "blocked",
            "model": "",
            "summary": job_id,
            "completion_preview": "",
            "source": "proposal_guard",
        }
    return receipt | {"status": "missing", "summary": "No matching DeepSeek result or queued job found yet"}


def _find_result(root: Path, job_id: str) -> dict[str, Any]:
    for row in reversed(_load_jsonl(root / "logs" / "deepseek_prompt_results.jsonl", 500)):
        if str(row.get("job_id") or "") == job_id:
            return row
    latest = _load_json(root / "logs" / "deepseek_prompt_latest_result.json")
    if str(latest.get("job_id") or "") == job_id:
        return latest
    return {}


def _find_queued(root: Path, job_id: str, file_path: str) -> dict[str, Any]:
    sources = [
        root / "logs" / "deepseek_code_completion_jobs.jsonl",
        root / "logs" / "deepseek_prompt_jobs.jsonl",
    ]
    for source in sources:
        for row in reversed(_load_jsonl(source, 500)):
            if str(row.get("job_id") or "") == job_id:
                return row | {"_source": str(source.relative_to(root))}
    latest = _load_json(root / "logs" / "deepseek_code_completion_latest.json")
    if str(latest.get("job_id") or "") == job_id or (file_path and latest.get("file") == file_path):
        return latest | {"_source": "logs/deepseek_code_completion_latest.json"}
    return {}


def _load_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        row = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}
    return row if isinstance(row, dict) else {}


def _empty(job_id: str) -> dict[str, Any]:
    return {"job_id": job_id, "status": "none", "model": "", "summary": "", "completion_preview": "", "source": ""}


def _snip(value: object, limit: int = 700) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


__all__ = ["resolve_deepseek_receipt"]
