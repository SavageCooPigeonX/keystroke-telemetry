# ┌──────────────────────────────────────────────┐
# │  predictor — phantom electrons for speculative  │
# │  execution. pigeon_brain/flow                   │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-31T00:15:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  fix module fixation + confidence calibration
# ── /pulse ──
"""Fires phantom electrons using cognitive profile (no real task). Triggers:
state change, every N prompts, or module cluster (3+ refs). Cost: ~$0.03/phantom."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v004 | 259 lines | ~2,506 tokens
# DESC:   fires_phantom_electrons_using_cognitive
# INTENT: rework_signal_0
# LAST:   2026-03-30 @ 2c247ba
# SESSIONS: 5
# ──────────────────────────────────────────────
# ── pigeon: SEQ 009 | v001 | backprop_impl | 2026-03-25 ──
from __future__ import annotations

import hashlib
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
    """Extract cognitive trends from recent prompt journal entries + live telemetry."""
    if not journal_path.exists():
        return {"states": [], "modules": [], "avg_del": 0.0, "avg_wpm": 0.0}

    entries = []
    for line in journal_path.read_text(encoding="utf-8").strip().splitlines()[-n_recent:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not entries:
        return {"states": [], "modules": [], "avg_del": 0.0, "avg_wpm": 0.0}

    states = [e.get("cognitive_state", "unknown") for e in entries]
    all_modules: list[str] = []
    for e in entries:
        all_modules.extend(e.get("module_refs", []))
        for hm in e.get("hot_modules", []):
            all_modules.append(hm.get("module", ""))

    # Inject live hot_modules from prompt_telemetry + file_heat_map
    root = journal_path.parent.parent  # logs/ -> project root
    try:
        telem_path = root / "logs" / "prompt_telemetry_latest.json"
        if telem_path.exists():
            telem = json.loads(telem_path.read_text(encoding="utf-8"))
            for hm in telem.get("hot_modules", []):
                mod = hm.get("module", "")
                if mod:
                    all_modules.append(mod)
                    all_modules.append(mod)  # double-weight live signal
    except Exception:
        pass
    try:
        heat_path = root / "file_heat_map.json"
        if heat_path.exists():
            hm_data = json.loads(heat_path.read_text(encoding="utf-8"))
            for entry in hm_data.get("files", [])[:5]:
                mod = entry.get("file", "").replace(".py", "")
                mod = mod.split("/")[-1].split("_seq")[0] if mod else ""
                if mod:
                    all_modules.append(mod)
    except Exception:
        pass

    # Inject recently-edited modules from edit_pairs (actual edits > hesitation)
    try:
        pairs_path = root / "logs" / "edit_pairs.jsonl"
        if pairs_path.exists():
            for line in pairs_path.read_text(encoding="utf-8").strip().splitlines()[-10:]:
                try:
                    ep = json.loads(line)
                    mod = ep.get("file", "").replace(".py", "")
                    mod = mod.split("/")[-1].split("_seq")[0] if mod else ""
                    if mod:
                        all_modules.extend([mod, mod, mod])  # triple-weight
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    module_counts = Counter(m for m in all_modules if m)
    # Lower threshold: top-5 modules regardless of count (was: count >= 2 only)
    clusters = [m for m, _c in module_counts.most_common(5)]
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

    # Read current session_n from latest journal entry
    session_n_at = 0
    journal = root / "logs" / "prompt_journal.jsonl"
    if journal.exists():
        lines = journal.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            try:
                session_n_at = json.loads(lines[-1]).get("session_n", len(lines))
            except json.JSONDecodeError:
                session_n_at = len(lines)

    batch_ts = datetime.now(timezone.utc).isoformat()
    batch_id = hashlib.md5(f"{batch_ts}_{phantom_seed[:40]}".encode()).hexdigest()[:12]

    for mode in modes:
        if run_flow_fn is not None:
            packet = run_flow_fn(root, phantom_seed, mode=mode)
            task_output = packet.summary()
        else:
            task_output = {"mode": mode, "phantom_seed": phantom_seed}

        pred_id = hashlib.md5(f"{batch_id}_{mode}".encode()).hexdigest()[:12]
        prediction = {
            "prediction_id": pred_id,
            "batch_id": batch_id,
            "session_n_at": session_n_at,
            "phantom_seed": phantom_seed,
            "mode": mode,
            "trend": trend,
            "result": task_output,
            "confidence": _compute_confidence(trend, root),
            "ts": batch_ts,
            "scored": False,
        }
        predictions.append(prediction)

    # Cache predictions
    existing = load_predictions(root)
    existing.extend(predictions)
    save_predictions(root, existing)

    return predictions


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
                    # Blend: 40% raw signal, 60% empirical hit rate
                    score = score * 0.4 + hit_rate * 0.6
        except Exception:
            pass

    return min(round(score, 3), 0.75)  # hard cap — never claim >75% until we earn it
