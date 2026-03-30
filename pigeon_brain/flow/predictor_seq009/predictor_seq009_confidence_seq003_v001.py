"""predictor_seq009_confidence_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from collections import Counter
from typing import Any

def _compute_confidence(trend: dict[str, Any]) -> float:
    """Estimate prediction confidence from signal strength.
    Calibrated: raw signal strength, no inflation.
    """
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

    return min(round(score, 3), 0.75)  # hard cap — never claim >75% until we earn it
