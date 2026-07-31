"""opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _prompt_row(row: dict[str, Any]) -> dict[str, Any]:
    return {"ts": row.get("ts"), "session_n": row.get("session_n"), "intent": row.get("intent"), "state": row.get("cognitive_state"), "preview": row.get("msg", "")[:180]}


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _jsonl_tail(path: Path, count: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

SCHEMA = "opus_orchestrator_runtime/v1"

LATEST = "logs/opus_orchestrator_runtime_latest.json"

HISTORY = "logs/opus_orchestrator_runtime.jsonl"

MARKDOWN = "logs/opus_orchestrator_runtime.md"

MANIFEST_NOTE = "logs/opus_orchestrator_manifest_note.md"
