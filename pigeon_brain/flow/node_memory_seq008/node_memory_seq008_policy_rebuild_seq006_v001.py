"""node_memory_seq008_policy_rebuild_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from typing import Any

def _rebuild_policy(node: str, entries: list[dict]) -> dict[str, Any]:
    """Compress raw entries into a behavioral policy.

    CRITICAL: Scoring uses ONLY observation fields (measured truth).
    Hypotheses (LLM summaries) are stored for display but do NOT affect scores.
    This prevents hallucination → memory → scoring contamination.
    """
    if not entries:
        return {}

    # Exponential moving average for rolling score — observations only
    score = 0.5  # prior
    for e in entries:
        obs = e.get("observation", e)  # backward compat: fall back to flat fields
        credit = obs.get("credit_score", e.get("credit_score", 0.5))
        loss = obs.get("outcome_loss", e.get("outcome_loss", 0.5))
        signal = credit * (1.0 - loss)
        score = score * (1.0 - DECAY_ALPHA) + signal * DECAY_ALPHA

    n = len(entries)
    confidence = min(n / MIN_CONFIDENCE_SAMPLES, 1.0)

    # Utilization = average credit score (from observations only)
    avg_credit = sum(
        e.get("observation", e).get("credit_score", e.get("credit_score", 0))
        for e in entries
    ) / n

    # Top effective patterns: entries with high credit + low loss (observation-based)
    effective = sorted(entries, key=lambda e: (
        e.get("observation", e).get("credit_score", e.get("credit_score", 0))
        * (1.0 - e.get("observation", e).get("outcome_loss", e.get("outcome_loss", 0)))
    ), reverse=True)
    # Hypotheses shown for context but labeled as such
    top_patterns = []
    for e in effective[:3]:
        obs = e.get("observation", e)
        credit = obs.get("credit_score", e.get("credit_score", 0))
        if credit > 0.3:
            hyp = e.get("hypothesis", {})
            summary = hyp.get("contribution_summary", e.get("contribution_summary", ""))
            top_patterns.append(summary)

    # Failure patterns: entries with low credit or high loss (observation-based)
    failures = sorted(entries, key=lambda e: (
        e.get("observation", e).get("outcome_loss", e.get("outcome_loss", 0))
        - e.get("observation", e).get("credit_score", e.get("credit_score", 0))
    ), reverse=True)
    fail_patterns = []
    for e in failures[:2]:
        obs = e.get("observation", e)
        loss = obs.get("outcome_loss", e.get("outcome_loss", 0))
        if loss > 0.5:
            hyp = e.get("hypothesis", {})
            summary = hyp.get("contribution_summary", e.get("contribution_summary", ""))
            fail_patterns.append(summary)

    # Behavioral directive
    directive = _synthesize_directive(node, score, top_patterns, fail_patterns)

    return {
        "node": node,
        "rolling_score": round(score, 4),
        "confidence": round(confidence, 4),
        # ── observation-derived (drives all decisions) ──
        "utilization_rate": round(avg_credit, 4),
        "sample_count": n,
        # ── hypothesis-derived (display only, NOT used for scoring) ──
        "top_effective_patterns": top_patterns,
        "failure_patterns": fail_patterns,
        "behavioral_directive": directive,
        # ── provenance ──
        "scoring_source": "observation_only",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
