"""predictor_seq009_confidence_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

def _compute_confidence(trend: dict[str, Any], root: Path | None = None) -> float:
    """Estimate prediction confidence from signal strength + historical accuracy."""
    score = 0.1  # low base — we haven't earned confidence yet

    # More data = modest boost (cap 0.15)
    n = trend.get("n_entries", 0)
    score += min(n / 30, 0.15)

    # Strong module clustering = moderate boost (cap 0.25)
    modules = trend.get("modules", [])
    score += min(len(modules) * 0.05, 0.25)

    # Consistent state = small boost (cap 0.15)
    states = trend.get("states", [])
    if states:
        dominant_count = Counter(states).most_common(1)[0][1]
        consistency = dominant_count / len(states)
        score += consistency * 0.15

    # High deletion = uncertainty, penalize
    if trend.get("avg_del", 0) > 0.3:
        score *= 0.7

    # Calibrate against historical prediction accuracy
    if root:
        try:
            scores_path = root / "pigeon_brain" / "prediction_scores.json"
            if scores_path.exists():
                scored = json.loads(scores_path.read_text(encoding="utf-8")).get("scores", [])
                if len(scored) >= 10:
                    recent = scored[-50:]
                    hit_rate = sum(1 for s in recent if s.get("score", {}).get("f1", 0) > 0) / len(recent)
                    score = score * 0.4 + hit_rate * 0.6
        except Exception:
            pass

    return min(round(score, 3), 0.75)  # hard cap — never claim >75% until we earn it
