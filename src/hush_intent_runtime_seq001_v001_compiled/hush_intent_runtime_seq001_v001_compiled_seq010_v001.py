"""hush_intent_runtime_seq001_v001_compiled_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

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


SCHEMA = "hush_intent_runtime/v1"

LATEST = "logs/hush_intent_runtime_latest.json"

HISTORY = "logs/hush_intent_runtime.jsonl"

MARKDOWN = "logs/hush_intent_runtime.md"


LOCAL_REPO = "keystroke_telemetry"

LOW_CONFIDENCE = 0.22

CROSS_REPO_MARGIN = 0.08


LOCAL_TERMS = {
    "keystroke", "telemetry", "file", "files", "sim", "orchestrator",
    "opus", "runtime", "prompt", "encoding", "intent", "context0",
    "rename", "inator", "deepseek", "copilot", "codex", "pigeon",
    "micro", "agents", "substrate", "mail", "email",
}

MAIF_TERMS = {
    "maif", "myaifingerprint", "linkrouter", "hush", "entity",
    "entities", "directory", "audit", "auditor", "consensus", "drift",
    "whisperer", "whisper", "irt", "field", "reputation",
}
