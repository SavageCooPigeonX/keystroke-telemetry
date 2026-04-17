"""push_snapshot_health_score_decomposed_seq012_v001.py — Honest health score.

Rebuilt per FIX_PLAN.md §1. Two-phase model:
  Phase 1: veto gates — any failure caps the score
  Phase 2: graded components (outcome-based, not activity-based)

Probe bonus deleted (probes are questions not answers).
Sync-score-low is now a PENALTY not a bonus.
Master test failure caps score at 50.
Sync tiered 2026-04-17: very-low (<0.03) caps at 55; low (<0.1) caps at 80.
A young project with 50+ modules and real work shouldn't be stuck at 60 forever.
"""

import json
from pathlib import Path

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-17T15:45:00Z
# EDIT_HASH: auto
# EDIT_WHY:  tier sync veto + compression ratchet
# ── /pulse ──

_ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _veto_caps(snapshot: dict) -> list[tuple[str, int]]:
    """Return list of (reason, cap) pairs. Lowest cap wins."""
    caps: list[tuple[str, int]] = []

    # Tiered sync veto (was flat 60 at <0.1 — too punishing for young projects)
    sync = snapshot.get("cycle", {}).get("sync_score", 0) or 0
    if sync < 0.03:
        caps.append(("sync_very_low", 55))
    elif sync < 0.1:
        caps.append(("sync_low", 80))

    # Rework rate from canonical source
    card = _read_json(_ROOT / "logs" / "rework_scorecard.json")
    if card:
        rate = float(card.get("rate", 0) or 0)
        if rate > 0.20:
            caps.append(("rework_too_high", 60))

    # Chronic bugs
    chronic = snapshot.get("bugs", {}).get("chronic_count", 0) or 0
    if chronic >= 3:
        caps.append(("chronic_bugs", 70))

    # Overcap epidemic — computed live from snapshot or 0
    overcap_hard = snapshot.get("modules", {}).get("overcap_hard_count", 0) or 0
    if overcap_hard > 10:
        caps.append(("overcap_epidemic", 65))

    # Shrink gate: if compression went backwards, cap hard
    shrink = _read_json(_ROOT / "logs" / "shrink_report.json")
    if shrink and shrink.get("status") == "blocked":
        caps.append(("shrink_gate_failed", 55))

    # Master test veto
    run = _read_json(_ROOT / "logs" / "master_run.json")
    if run is None:
        caps.append(("master_test_missing", 50))
    elif not run.get("passed", False):
        caps.append(("master_test_failed", 50))
    elif not run.get("integrity_ok", False):
        caps.append(("master_test_integrity_fail", 50))

    return caps


def _compliance_component(snapshot: dict) -> float:
    compliance = snapshot.get("modules", {}).get("compliance_pct", 0) or 0
    return (compliance / 100) * 20  # max +20


def _outcome_component(snapshot: dict) -> float:
    """Actual fix rate from self_fix_verification.jsonl. Max +15."""
    log = _ROOT / "logs" / "self_fix_verification.jsonl"
    if not log.exists():
        return 0.0
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return 0.0
    recent = lines[-10:]
    closed_total = touched_total = 0
    for ln in recent:
        try:
            r = json.loads(ln)
            closed_total += r.get("closed_count", 0)
            touched_total += r.get("touched_count", 0)
        except Exception:
            pass
    if touched_total == 0:
        return 0.0
    return min(closed_total / touched_total, 1.0) * 15


def _drift_component(snapshot: dict) -> float:
    """Prompt↔code sync. Max +10 at sync>=0.5."""
    sync = snapshot.get("cycle", {}).get("sync_score", 0) or 0
    return min(sync * 20, 10)


def _staleness_component(snapshot: dict) -> float:
    """Penalty for stale pipelines. Max -10."""
    hours = snapshot.get("staleness", {}).get("max_hours_since_update", 0) or 0
    if hours > 48:
        return 10
    if hours > 24:
        return 5
    return 0


def _recurrence_component(snapshot: dict) -> float:
    """Penalty for chronic bugs surviving >=3 cycles. Max -10."""
    chronic = snapshot.get("bugs", {}).get("chronic_count", 0) or 0
    return min(chronic * 2, 10)


def _contradiction_component(snapshot: dict) -> float:
    """Penalty for numeric contradictions across blocks. Max -5."""
    count = snapshot.get("contradictions", {}).get("count", 0) or 0
    return min(count, 5)


def _shrink_component() -> float:
    """Bonus for actively shrinking codebase. Max +8.

    +5 if shrink gate is green (no growth)
    +3 extra if we ratcheted the overcap budget DOWN this push
    """
    report = _read_json(_ROOT / "logs" / "shrink_report.json")
    if not report or report.get("status") != "ok":
        return 0.0
    bonus = 5.0
    before = report.get("ratchet_budget_before")
    after = report.get("ratchet_budget_after")
    if isinstance(before, int) and isinstance(after, int) and after < before:
        bonus += 3.0
    return bonus


def _compute_health_score(snapshot: dict) -> float:
    """Honest two-phase health score. Score cannot exceed lowest veto cap."""
    caps = _veto_caps(snapshot)

    score = 50.0
    score += _compliance_component(snapshot)
    score += _outcome_component(snapshot)
    score += _drift_component(snapshot)
    score += _shrink_component()
    score -= _staleness_component(snapshot)
    score -= _recurrence_component(snapshot)
    score -= _contradiction_component(snapshot)

    score = max(0.0, min(100.0, score))
    if caps:
        cap_value = min(c for _, c in caps)
        score = min(score, cap_value)

    return round(score, 1)


def compute_health_score_with_caps(snapshot: dict) -> tuple[float, list[tuple[str, int]]]:
    """Verbose variant — returns (score, applied_caps) for diagnostics."""
    caps = _veto_caps(snapshot)
    score = _compute_health_score(snapshot)
    return score, caps
