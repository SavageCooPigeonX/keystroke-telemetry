"""prediction_scorer_seq014_calibration_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v002 | 45 lines | ~419 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _update_calibration(root: Path, scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Track confidence vs actual scores for calibration.

    Stores running stats: how often high-confidence predictions are right.
    """
    p = _calibration_path(root)
    if p.exists():
        cal = json.loads(p.read_text(encoding="utf-8"))
    else:
        cal = {"buckets": {}, "total": 0, "overconfidence_rate": 0.0}

    for s in scored:
        conf = s.get("confidence", 0.5)
        actual = s.get("score", {}).get("combined", 0.0)
        # Bucket confidence into 0.1 ranges
        bucket = str(round(conf, 1))
        b = cal["buckets"].setdefault(bucket, {"count": 0, "sum_actual": 0.0, "sum_conf": 0.0})
        b["count"] += 1
        b["sum_actual"] += actual
        b["sum_conf"] += conf
        cal["total"] += 1

    # Compute overconfidence rate
    overconfident = 0
    total = 0
    for bk, bv in cal["buckets"].items():
        if bv["count"] > 0:
            avg_actual = bv["sum_actual"] / bv["count"]
            avg_conf = bv["sum_conf"] / bv["count"]
            if avg_conf > avg_actual + 0.2:
                overconfident += bv["count"]
            total += bv["count"]
    cal["overconfidence_rate"] = round(overconfident / max(total, 1), 3)
    cal["updated_at"] = datetime.now(timezone.utc).isoformat()

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cal, indent=2, default=str), encoding="utf-8")
    return cal
