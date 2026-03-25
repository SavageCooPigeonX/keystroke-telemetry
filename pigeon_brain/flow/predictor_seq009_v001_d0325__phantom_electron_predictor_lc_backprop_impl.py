# ┌──────────────────────────────────────────────┐
# │  predictor — phantom electrons for speculative  │
# │  execution. pigeon_brain/flow                   │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-25T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  trim to 200 lines
# ── /pulse ──
"""Fires phantom electrons using cognitive profile (no real task). Triggers:
state change, every N prompts, or module cluster (3+ refs). Cost: ~$0.03/phantom."""
# ── pigeon: SEQ 009 | v001 | backprop_impl | 2026-03-25 ──
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PREDICTION_CACHE_FILE = "prediction_cache.json"
DEFAULT_PREDICTION_INTERVAL = 10  # every N prompts
MODULE_CLUSTER_THRESHOLD = 3       # N+ refs to trigger prediction


def _cache_path(root: Path) -> Path:
    return root / "pigeon_brain" / PREDICTION_CACHE_FILE


def load_predictions(root: Path) -> list[dict[str, Any]]:
    """Load cached predictions."""
    p = _cache_path(root)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("predictions", [])
    return []


def save_predictions(root: Path, predictions: list[dict[str, Any]]) -> None:
    """Persist prediction cache."""
    p = _cache_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(
        {"predictions": predictions[-50:], "updated": datetime.now(timezone.utc).isoformat()},
        indent=2, default=str,
    ), encoding="utf-8")


def extract_cognitive_trend(journal_path: Path, n_recent: int = 10) -> dict[str, Any]:
    """Extract cognitive trends from recent prompt journal entries."""
    if not journal_path.exists():
        return {"states": [], "modules": [], "avg_del": 0.0, "avg_wpm": 0.0}

    entries = []
    for line in journal_path.read_text(encoding="utf-8").strip().splitlines()[-n_recent:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Module frequency distribution
    if not entries:
        return {"states": [], "modules": [], "avg_del": 0.0, "avg_wpm": 0.0}
    states = [e.get("cognitive_state", "unknown") for e in entries]
    all_modules: list[str] = []
    for e in entries:
        all_modules.extend(e.get("module_refs", []))
        for hm in e.get("hot_modules", []):
            all_modules.append(hm.get("module", ""))
    module_counts = Counter(m for m in all_modules if m)
    clusters = [m for m, c in module_counts.most_common(5) if c >= 2]
    signals = [e.get("signals", {}) for e in entries]
    avg_del = sum(s.get("deletion_ratio", 0) for s in signals) / max(len(signals), 1)
    avg_wpm = sum(s.get("wpm", 0) for s in signals) / max(len(signals), 1)
    return {
        "states": states, "modules": clusters,
        "avg_del": round(avg_del, 4), "avg_wpm": round(avg_wpm, 1),
        "dominant_state": Counter(states).most_common(1)[0][0] if states else "unknown",
        "n_entries": len(entries),
    }


def should_predict(root: Path, prompt_count: int, interval: int = DEFAULT_PREDICTION_INTERVAL) -> bool:
    """Check if we should fire a prediction cycle."""
    if prompt_count > 0 and prompt_count % interval == 0:
        return True
    # Also check for module clustering
    journal = root / "logs" / "prompt_journal.jsonl"
    trend = extract_cognitive_trend(journal, n_recent=5)
    if len(trend.get("modules", [])) >= MODULE_CLUSTER_THRESHOLD:
        return True
    return False


def synthesize_phantom_seed(trend: dict[str, Any]) -> str:
    """Create a task seed from cognitive profile instead of a real task."""
    parts: list[str] = []
    state = trend.get("dominant_state", "unknown")
    modules = trend.get("modules", [])
    state_map = {
        "frustrated": "Operator frustrated, likely needs debugging help",
        "focused": "Operator in flow, likely building new feature",
        "hesitant": "Operator uncertain, likely needs guidance",
    }
    parts.append(state_map.get(state, "Predict operator's next need"))
    if modules:
        parts.append(f"Module focus: {', '.join(modules[:3])}")
    if trend.get("avg_del", 0) > 0.3:
        parts.append("High deletion ratio suggests rework/frustration")
    return ". ".join(parts)


def predict_next_needs(
    root: Path, run_flow_fn: Any = None, n_predictions: int = 3,
) -> list[dict[str, Any]]:
    """Fire phantom electrons based on cognitive profile."""
    journal = root / "logs" / "prompt_journal.jsonl"
    trend = extract_cognitive_trend(journal)
    if trend.get("n_entries", 0) < 3:
        return []
    phantom_seed = synthesize_phantom_seed(trend)
    predictions: list[dict[str, Any]] = []

    modes = ["targeted", "heat", "failure"][:n_predictions]

    for mode in modes:
        if run_flow_fn is not None:
            packet = run_flow_fn(root, phantom_seed, mode=mode)
            task_output = packet.summary()
        else:
            task_output = {"mode": mode, "phantom_seed": phantom_seed}

        prediction = {
            "phantom_seed": phantom_seed,
            "mode": mode,
            "trend": trend,
            "result": task_output,
            "confidence": _compute_confidence(trend),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        predictions.append(prediction)

    # Cache predictions
    existing = load_predictions(root)
    existing.extend(predictions)
    save_predictions(root, existing)

    return predictions


def _compute_confidence(trend: dict[str, Any]) -> float:
    """Estimate prediction confidence from signal strength."""
    score = 0.3  # base

    # More data = more confidence
    n = trend.get("n_entries", 0)
    score += min(n / 20, 0.3)

    # Strong module clustering = higher confidence
    modules = trend.get("modules", [])
    score += min(len(modules) * 0.1, 0.2)

    # Consistent state = higher confidence
    states = trend.get("states", [])
    if states:
        dominant_count = Counter(states).most_common(1)[0][1]
        consistency = dominant_count / len(states)
        score += consistency * 0.2

    return min(round(score, 3), 1.0)
