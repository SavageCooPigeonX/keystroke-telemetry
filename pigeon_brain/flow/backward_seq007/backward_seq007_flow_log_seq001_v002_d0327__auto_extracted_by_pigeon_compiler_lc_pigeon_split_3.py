"""backward_seq007_flow_log_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 50 lines | ~423 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import json
import re
import uuid

def _flow_log_path(root: Path) -> Path:
    return root / "pigeon_brain" / FLOW_LOG


def log_forward_pass(root: Path, packet_summary: dict[str, Any]) -> str:
    """Record a forward pass in the flow log. Returns the electron_id."""
    electron_id = packet_summary.get("electron_id") or uuid.uuid4().hex[:12]
    packet_summary["electron_id"] = electron_id
    p = _flow_log_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(packet_summary, default=str) + "\n")
    return electron_id


def _load_forward_path(root: Path, electron_id: str) -> dict[str, Any] | None:
    """Find a forward pass record by electron_id."""
    p = _flow_log_path(root)
    if not p.exists():
        return None
    for line in reversed(p.read_text(encoding="utf-8").strip().splitlines()):
        try:
            record = json.loads(line)
            if record.get("electron_id") == electron_id:
                return record
        except json.JSONDecodeError:
            continue
    return None


def _append_insight(root: Path, electron_id: str, insight: str, loss: float) -> None:
    """Append a DeepSeek system insight to the flow log."""
    p = _flow_log_path(root)
    entry = {
        "type": "backward_insight",
        "electron_id": electron_id,
        "insight": insight[:300],
        "loss": round(loss, 4),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")

FLOW_LOG = "flow_log.jsonl"
