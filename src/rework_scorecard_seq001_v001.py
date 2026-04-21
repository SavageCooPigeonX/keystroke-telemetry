"""rework_scorecard_seq001_v001 — single source of truth for AI rework rate.

Solves the multi-block contradiction surfaced in copilot-instructions.md
where 4 different sections report 4 different rework rates (0% / 4% / 5.5% / 69%).

Writes logs/rework_scorecard_seq001_v001.json. All managed prompt blocks MUST read from
this file rather than computing their own slice.

Usage:
    from src.rework_scorecard_seq001_v001 import update_scorecard, load_scorecard
    update_scorecard(total=200, missed=16)  # -> rate=0.08
    card = load_scorecard()  # {'total': 200, 'missed': 16, 'rate': 0.08, 'updated_ts': ...}
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-16T00:00:00Z
# EDIT_HASH: auto
# EDIT_WHY:  unify rework rate source
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

SCORECARD = Path("logs/rework_scorecard_seq001_v001.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_scorecard(total: int, missed: int, notes: str = "") -> dict:
    """Write a new scorecard snapshot. Single canonical source."""
    total = max(int(total), 0)
    missed = max(int(missed), 0)
    rate = (missed / total) if total > 0 else 0.0
    card = {
        "total": total,
        "missed": missed,
        "rate": round(rate, 4),
        "updated_ts": _now(),
        "notes": notes,
    }
    SCORECARD.parent.mkdir(parents=True, exist_ok=True)
    SCORECARD.write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card


def load_scorecard() -> dict | None:
    if not SCORECARD.exists():
        return None
    try:
        return json.loads(SCORECARD.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_rework_rate() -> float:
    """Canonical reader for any prompt block or scorer. Returns 0.0 if unknown."""
    card = load_scorecard()
    if card is None:
        return 0.0
    return float(card.get("rate", 0.0))
