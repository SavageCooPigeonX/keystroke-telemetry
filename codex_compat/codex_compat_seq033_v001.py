"""codex_compat_seq033_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _load_jsonl_tail
from pathlib import Path
from typing import Any
import json
import re

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _next_session_n(root: Path) -> int:
    rows = _load_jsonl_tail(root / "logs" / "prompt_journal.jsonl", max_lines=1)
    if not rows:
        return 1
    try:
        return int(rows[-1].get("session_n", 0)) + 1
    except (TypeError, ValueError):
        return 1


def _classify_intent(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in (
        "orchestrator", "10q", "consensus", "approval", "approve", "guard",
        "copilot", "deepseek", "file sim", "file_sim", "autonomous",
    )):
        return "orchestration"
    if any(word in text for word in ("email", "emails", "resend", "outbox", "alert", "alerts")):
        return "telemetry"
    if any(word in text for word in ("monitor", "watch", "observe", "observatory")):
        return "monitoring"
    if any(word in text for word in ("fix", "bug", "error", "broken", "wrong", "fail")):
        return "debugging"
    if any(word in text for word in ("add", "create", "build", "implement", "wire")):
        return "building"
    if any(word in text for word in ("refactor", "rename", "move", "split", "cleanup")):
        return "restructuring"
    if any(word in text for word in ("test", "verify", "check", "run")):
        return "testing"
    if any(word in text for word in ("why", "how", "what", "explain", "analyze", "inspect")):
        return "exploring"
    return "unknown"
