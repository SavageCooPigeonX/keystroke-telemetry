"""learning_loop_seq013_state_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 36 lines | ~284 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import time

def _state_path(root: Path) -> Path:
    return root / "pigeon_brain" / LOOP_STATE_FILE


def _load_state(root: Path) -> dict[str, Any]:
    """Load loop state: tracks which journal entries have been processed."""
    p = _state_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "last_processed_ts": None,
        "last_processed_line": 0,
        "total_cycles": 0,
        "total_forward": 0,
        "total_backward": 0,
        "total_predictions": 0,
        "total_cost": 0.0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


def _save_state(root: Path, state: dict[str, Any]) -> None:
    p = _state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


LOOP_STATE_FILE = "learning_loop_state.json"
