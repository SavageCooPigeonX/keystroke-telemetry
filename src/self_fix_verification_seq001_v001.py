"""self_fix_verification_seq001_v001 — the missing verify step for self_fix.

Closes the open-ended loop in FIX_PLAN.md §2:
    scan → fix → [VERIFY here] → escalate_persisted

Call `record_verification()` after every auto-apply batch. Writes JSONL append-only
so history cannot be retroactively edited to fake a passing record.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-16T00:00:00Z
# EDIT_HASH: auto
# EDIT_WHY:  close self_fix verify loop
# ── /pulse ──

VERIFICATION_LOG = Path("logs/self_fix_verification_seq001_v001.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_verification(
    *,
    before_bugs: set[str] | list[str],
    after_bugs: set[str] | list[str],
    touched_files: list[str],
    fix_type: str,
    rolled_back: list[str] | None = None,
) -> dict:
    """Record a fix-verification entry. Returns the written record."""
    before_set = set(before_bugs)
    after_set = set(after_bugs)
    closed = sorted(before_set - after_set)
    persisted = sorted(before_set & after_set)
    new_bugs = sorted(after_set - before_set)
    record = {
        "ts": _now(),
        "fix_type": fix_type,
        "touched_count": len(touched_files),
        "touched": list(touched_files)[:20],
        "before_count": len(before_set),
        "after_count": len(after_set),
        "closed": closed,
        "closed_count": len(closed),
        "persisted": persisted,
        "persisted_count": len(persisted),
        "new_bugs_introduced": new_bugs,
        "regression_count": len(new_bugs),
        "rolled_back": rolled_back or [],
    }
    VERIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with VERIFICATION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def recent_close_rate(last_n: int = 10) -> float:
    """Average close-rate across last N verifications. Feeds health score."""
    if not VERIFICATION_LOG.exists():
        return 0.0
    lines = [l for l in VERIFICATION_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return 0.0
    recent = [json.loads(l) for l in lines[-last_n:]]
    rates = []
    for r in recent:
        touched = max(r.get("touched_count", 0), 1)
        rates.append(r.get("closed_count", 0) / touched)
    return sum(rates) / len(rates) if rates else 0.0


def regression_count(last_n: int = 10) -> int:
    """Sum of regressions in last N verifications. Should always be 0."""
    if not VERIFICATION_LOG.exists():
        return 0
    lines = [l for l in VERIFICATION_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    recent = [json.loads(l) for l in lines[-last_n:]]
    return sum(r.get("regression_count", 0) for r in recent)
