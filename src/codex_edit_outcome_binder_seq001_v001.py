"""Bind accepted Codex edits into edit-pair and training-pair telemetry."""
from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LATEST = "logs/codex_edit_outcome_latest.json"
HISTORY = "logs/codex_edit_outcomes.jsonl"


def bind_codex_edit_outcome(
    root: Path,
    files: list[str],
    *,
    reason: str = "accepted Codex edit outcome",
    source: str = "codex_runtime",
    capture_training: bool = True,
    write: bool = True,
) -> dict[str, Any]:
    """Append fresh edit_pairs rows, then capture training rows from them."""
    root = Path(root)
    prompt = _latest_jsonl(root / "logs" / "prompt_journal.jsonl")
    now = datetime.now(timezone.utc).isoformat()
    rows = [_edit_pair(root, file, prompt, now, reason, source) for file in _valid_files(root, files)]
    captured = []
    if write and rows:
        for row in rows:
            _append_jsonl(root / "logs" / "edit_pairs.jsonl", row)
            if capture_training:
                pair = _capture_training_pair(root)
                if pair:
                    captured.append(_training_summary(pair))
        payload = _payload(now, prompt, rows, captured, reason, source)
        _write_json(root / LATEST, payload)
        _append_jsonl(root / HISTORY, payload)
        return payload
    return _payload(now, prompt, rows, captured, reason, source)


def _edit_pair(root: Path, file: str, prompt: dict[str, Any], now: str, reason: str, source: str) -> dict[str, Any]:
    prompt_ts = prompt.get("ts", "")
    return {
        "ts": now,
        "prompt_ts": prompt_ts,
        "prompt_msg": str(prompt.get("msg", ""))[:240],
        "file": file,
        "edit_ts": now,
        "edit_why": reason,
        "edit_hash": "codex",
        "latency_ms": _latency_ms(prompt_ts, now),
        "state": prompt.get("cognitive_state", "unknown"),
        "session_n": prompt.get("session_n", 0),
        "source": source,
        "file_email": {
            "schema": "file_email/v1",
            "trigger": "codex_edit_outcome",
            "event_type": "touch",
            "file": file,
            "decision": "accepted",
            "reason": reason,
            "validation_plan": ["git diff --check"],
        },
    }


def _capture_training_pair(root: Path) -> dict[str, Any] | None:
    try:
        module = importlib.import_module("src.对p_tp_s027_v003_d0402_缩分话_λVR_βoc")
        return module.capture_training_pair(root)
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _payload(now: str, prompt: dict[str, Any], rows: list[dict[str, Any]], captured: list[dict[str, Any]], reason: str, source: str) -> dict[str, Any]:
    return {
        "schema": "codex_edit_outcome/v1",
        "ts": now,
        "source": source,
        "reason": reason,
        "prompt_session": prompt.get("session_n", 0),
        "prompt_ts": prompt.get("ts", ""),
        "files": [row["file"] for row in rows],
        "edit_pairs_written": len(rows),
        "training_pairs_captured": len([row for row in captured if not row.get("error")]),
        "training_capture": captured,
    }


def _training_summary(pair: dict[str, Any]) -> dict[str, Any]:
    if pair.get("error"):
        return pair
    return {
        "ts": pair.get("ts"),
        "session_n": pair.get("session_n"),
        "file": (pair.get("copilot_intent") or {}).get("file", ""),
        "response_captured": (pair.get("alignment") or {}).get("response_captured", False),
    }


def _valid_files(root: Path, files: list[str]) -> list[str]:
    out = []
    for file in files:
        clean = str(file).replace("\\", "/").strip()
        if clean and (root / clean).exists() and clean not in out:
            out.append(clean)
    return out


def _latest_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    for line in reversed(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {}


def _latency_ms(start: str, end: str) -> int:
    try:
        a = datetime.fromisoformat(start.replace("Z", "+00:00"))
        b = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return int((b - a).total_seconds() * 1000)
    except ValueError:
        return 0


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")
