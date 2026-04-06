# ┌──────────────────────────────────────────────┐
# │  prediction_scorer — compares phantom          │
# │  predictions against actual edit sessions +    │
# │  rework signals. pigeon_brain/flow             │
# └──────────────────────────────────────────────┘
"""
Prediction scorer v2 — edit-session based.

Scores predictions against THREE reality signals:
  1. edit_pairs.jsonl — which files did Copilot actually edit after each prompt?
  2. rework_log.json — did the edit land? (miss/partial/ok)
  3. git diff — delayed commit-level audit (secondary)

Predictions bind to prompts via session_n. When a prediction fires at
session_n=10, the next N edits (session_n 11..15) are the evaluation window.
If predicted modules appear in those edits, the prediction hit.
If the rework verdict for those edits was "ok", the prediction was useful.

Confidence calibration: tracks predicted confidence vs actual F1 over time,
penalizes overconfident wrong predictions harder.
"""

# ── pigeon: SEQ 014 | v002 | edit_session_scoring | 2026-03-27 ──
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCORED_CACHE_FILE = "prediction_scores.json"
CALIBRATION_FILE = "prediction_calibration.json"
MAX_SCORED = 200
EVAL_WINDOW = 5  # score against next N prompts after prediction


def _scores_path(root: Path) -> Path:
    return root / "pigeon_brain" / SCORED_CACHE_FILE


def _calibration_path(root: Path) -> Path:
    return root / "pigeon_brain" / CALIBRATION_FILE


def _load_scores(root: Path) -> list[dict[str, Any]]:
    p = _scores_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8")).get("scores", [])
    return []


def _save_scores(root: Path, scores: list[dict[str, Any]]) -> None:
    p = _scores_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"scores": scores[-MAX_SCORED:],
            "updated_at": datetime.now(timezone.utc).isoformat()}
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# ── Reality signal loaders ──

def _load_edit_pairs(root: Path) -> list[dict[str, Any]]:
    """Load all edit pairs (prompt→file edit bindings)."""
    p = root / "logs" / "edit_pairs.jsonl"
    if not p.exists():
        return []
    pairs = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        try:
            pairs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return pairs


def _load_rework_log(root: Path) -> list[dict[str, Any]]:
    """Load rework verdicts."""
    p = root / "rework_log.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("entries", data.get("events", []))


def _load_copilot_edits(root: Path) -> list[dict[str, Any]]:
    """Load copilot/AI edit events from the VS Code extension.

    These are large text insertions (>=8 chars or multi-line) captured by
    onDidChangeTextDocument — the primary source of file mutations in an
    AI-assisted workflow. Includes Copilot inline completions, Chat Apply,
    Edits mode, and paste operations.
    """
    p = root / "logs" / "copilot_edits.jsonl"
    if not p.exists():
        return []
    edits = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        try:
            edits.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return edits


def _get_copilot_edit_modules_in_window(
    copilot_edits: list[dict[str, Any]],
    after_ts_ms: float,
    window_ms: float = 600_000,  # 10 min default window
) -> set[str]:
    """Get modules that had AI edits in a time window.

    Returns set of module names extracted from copilot_edits.jsonl entries
    whose timestamp falls within (after_ts_ms, after_ts_ms + window_ms].
    """
    modules = set()
    for ce in copilot_edits:
        ts = ce.get("ts", 0)
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts).timestamp() * 1000
            except (ValueError, TypeError):
                continue
        if after_ts_ms < ts <= after_ts_ms + window_ms:
            mod = extract_module_name(ce.get("file", ""))
            if mod:
                modules.add(mod)
    return modules


def _load_unified_edits(root: Path) -> list[dict[str, Any]]:
    """Load unified edit events — the merged signal from all telemetry sources.

    This is the HIGHEST FIDELITY source of "what actually changed" because it
    merges copilot_edits, edit_pairs, AI response timing, and rework verdicts
    into a single correlated stream.

    Falls back to copilot_edits + edit_pairs if unified log doesn't exist yet.
    """
    p = root / "logs" / "unified_edits.jsonl"
    if not p.exists():
        return []
    edits = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        try:
            edits.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return edits


def _get_unified_modules_in_window(
    unified_edits: list[dict[str, Any]],
    after_ts_ms: float,
    window_ms: float = 600_000,
) -> tuple[set[str], dict[str, list[str]]]:
    """Get modules from unified edits in a time window.

    Returns (module_names, source_map) where source_map maps each module
    to the edit_source values that touched it.
    """
    modules: set[str] = set()
    source_map: dict[str, list[str]] = {}
    for ue in unified_edits:
        ts = ue.get("ts", 0)
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts).timestamp() * 1000
            except (ValueError, TypeError):
                continue
        if after_ts_ms < ts <= after_ts_ms + window_ms:
            mod = extract_module_name(ue.get("file", ""))
            if mod:
                modules.add(mod)
                src = ue.get("edit_source", "unknown")
                source_map.setdefault(mod, []).append(src)
    return modules, source_map


def _load_journal_window(root: Path, after_n: int, window: int) -> list[dict[str, Any]]:
    """Load journal entries in session_n range (after_n, after_n + window]."""
    p = root / "logs" / "prompt_journal.jsonl"
    if not p.exists():
        return []
    entries = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        try:
            e = json.loads(line)
            sn = e.get("session_n", 0)
            if after_n < sn <= after_n + window:
                entries.append(e)
        except json.JSONDecodeError:
            continue
    return entries


def extract_module_name(filepath: str) -> str | None:
    """Extract pigeon module name from a file path."""
    if not filepath.endswith(".py"):
        return None
    stem = Path(filepath).stem
    m = re.match(r"^\.?([a-zA-Z_][a-zA-Z0-9_]*)_seq\d+", stem)
    if m:
        return m.group(1)
    return stem


def _get_edit_session_modules(
    edit_pairs: list[dict[str, Any]], after_session_n: int, window: int,
) -> tuple[set[str], list[dict[str, Any]]]:
    """Get modules edited in the evaluation window after a prediction.

    Returns (module_names, matching_edit_pairs).
    """
    modules = set()
    matching = []
    for ep in edit_pairs:
        sn = ep.get("session_n", 0)
        if after_session_n < sn <= after_session_n + window:
            mod = extract_module_name(ep.get("file", ""))
            if mod:
                modules.add(mod)
            matching.append(ep)
    return modules, matching


def _get_rework_in_window(
    rework_entries: list[dict[str, Any]],
    journal_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Match rework verdicts to journal entries in the window by timestamp.

    Returns aggregated rework signal.
    """
    if not rework_entries or not journal_entries:
        return {"avg_rework": 0.0, "miss_rate": 0.0, "n_matched": 0}

    # Build timestamp set from journal entries (±2s tolerance)
    journal_ts_ms = []
    for je in journal_entries:
        ts = je.get("ts", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(ts)
            journal_ts_ms.append(dt.timestamp() * 1000)
        except (ValueError, TypeError):
            continue

    matched_rework = []
    for rw in rework_entries:
        rw_ts = rw.get("ts", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(rw_ts)
            rw_ms = dt.timestamp() * 1000
        except (ValueError, TypeError):
            continue
        # Match if rework ts is within 60s of any journal entry in window
        for jts in journal_ts_ms:
            if abs(rw_ms - jts) < 60_000:
                matched_rework.append(rw)
                break

    if not matched_rework:
        return {"avg_rework": 0.0, "miss_rate": 0.0, "n_matched": 0}

    scores = [r.get("rework_score", 0.0) for r in matched_rework]
    misses = sum(1 for r in matched_rework if r.get("verdict") == "miss")
    return {
        "avg_rework": round(sum(scores) / len(scores), 3),
        "miss_rate": round(misses / len(matched_rework), 3),
        "n_matched": len(matched_rework),
    }


# ── Scoring ──

def score_prediction(
    prediction: dict[str, Any],
    actual_modules: set[str],
    edit_pairs_in_window: list[dict[str, Any]],
    rework_signal: dict[str, Any],
) -> dict[str, Any]:
    """Score one prediction against edit-session reality + rework."""
    pred_result = prediction.get("result", {})
    pred_path = pred_result.get("path", [])
    pred_modules = set(pred_path)
    trend_modules = set(prediction.get("trend", {}).get("modules", []))
    pred_modules |= trend_modules

    if not pred_modules:
        return {**prediction, "score": {"f1": 0.0, "detail": "no_predicted_modules"}}

    hits = pred_modules & actual_modules
    misses = actual_modules - pred_modules
    false_pos = pred_modules - actual_modules

    precision = len(hits) / len(pred_modules) if pred_modules else 0.0
    recall = len(hits) / len(actual_modules) if actual_modules else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Outcome quality: did the edits in the window land well?
    rework_penalty = rework_signal.get("avg_rework", 0.0)
    miss_rate = rework_signal.get("miss_rate", 0.0)
    outcome_quality = max(0.0, 1.0 - rework_penalty - miss_rate * 0.5)

    # Combined score: module overlap + outcome quality
    combined = f1 * 0.6 + outcome_quality * 0.4

    # Confidence calibration error
    confidence = prediction.get("confidence", 0.5)
    calibration_error = abs(confidence - combined)

    return {
        "prediction_id": prediction.get("prediction_id", "?"),
        "batch_id": prediction.get("batch_id", "?"),
        "session_n_at": prediction.get("session_n_at", 0),
        "phantom_seed": prediction.get("phantom_seed", "")[:100],
        "mode": prediction.get("mode", "?"),
        "confidence": confidence,
        "ts_predicted": prediction.get("ts", ""),
        "ts_scored": datetime.now(timezone.utc).isoformat(),
        "score": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "outcome_quality": round(outcome_quality, 3),
            "combined": round(combined, 3),
            "calibration_error": round(calibration_error, 3),
            "rework_penalty": round(rework_penalty, 3),
            "hits": sorted(hits),
            "misses": sorted(misses)[:10],
            "false_positives": sorted(false_pos)[:10],
            "hit_count": len(hits),
            "miss_count": len(misses),
            "false_pos_count": len(false_pos),
            "edits_in_window": len(edit_pairs_in_window),
        },
        "predicted_path": pred_path[:10],
        "actual_modules": sorted(actual_modules)[:20],
    }


# ── Confidence calibration ──

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


# ── Node memory backfill ──

def backfill_prediction_scores(root: Path, scored: list[dict[str, Any]]) -> int:
    """Feed prediction accuracy into node_memory with calibration-weighted penalties."""
    from .node_memory_seq008 import append_learning  # pigeon package re-export

    updated = 0
    for s in scored:
        score_data = s.get("score", {})
        hits = score_data.get("hits", [])
        false_pos = score_data.get("false_positives", [])
        combined = score_data.get("combined", 0.0)
        cal_err = score_data.get("calibration_error", 0.0)
        seed = s.get("phantom_seed", "")[:80]
        eid = s.get("prediction_id", hashlib.md5(
            f"pred_{seed}_{s.get('ts_scored','')}".encode()).hexdigest()[:12])

        for node in hits:
            append_learning(
                root, node, eid,
                task_seed=seed,
                contribution_summary=f"pred_hit combined={combined:.2f}",
                credit_score=0.5 + combined * 0.4,
                outcome_loss=max(0.0, 0.3 - combined * 0.3),
            )
            updated += 1

        # Penalty scales with calibration error
        penalty_loss = min(0.7, 0.3 + cal_err * 0.4)
        for node in false_pos[:5]:
            append_learning(
                root, node, eid,
                task_seed=seed,
                contribution_summary=f"pred_false_pos cal_err={cal_err:.2f}",
                credit_score=0.15,
                outcome_loss=penalty_loss,
            )
            updated += 1

    return updated


# ── Main entry points ──

def score_predictions_post_edit(root: Path) -> dict[str, Any]:
    """Score predictions against edit sessions (primary scoring method).

    Uses THREE reality signals:
      1. copilot_edits.jsonl — AI/Copilot file mutations (PRIMARY, real-time)
      2. edit_pairs.jsonl — pulse-harvested prompt→file bindings
      3. rework_log.json — did the edit land? (miss/partial/ok)

    Should be called frequently (every prediction cycle in the learning loop).
    """
    from .预p_pr_s009_v004_d0330_踪稿析_λρ import (
        load_predictions, save_predictions,
    )

    predictions = load_predictions(root)
    if not predictions:
        return {"status": "no_predictions", "scored": 0}

    edit_pairs = _load_edit_pairs(root)
    copilot_edits = _load_copilot_edits(root)
    unified_edits = _load_unified_edits(root)
    rework_entries = _load_rework_log(root)

    # Only score predictions that haven't been scored yet
    unscored = [p for p in predictions if not p.get("scored")]
    if not unscored:
        return {"status": "all_scored", "scored": 0}

    # Need enough subsequent data to evaluate — check both sources
    max_session_n = max(
        (ep.get("session_n", 0) for ep in edit_pairs), default=0
    )
    # Also check if we have copilot edits (timestamp-based)
    max_copilot_ts = max(
        (ce.get("ts", 0) for ce in copilot_edits), default=0
    )

    scored_results = []
    newly_scored_ids = set()

    for pred in unscored:
        pred_sn = pred.get("session_n_at", 0)
        pred_ts = pred.get("ts", "")

        # Convert prediction timestamp to epoch ms for time-windowed matching
        pred_ts_ms = 0.0
        if pred_ts:
            try:
                pred_ts_ms = datetime.fromisoformat(pred_ts).timestamp() * 1000
            except (ValueError, TypeError):
                pass

        # ── TIER 1: Unified edits (highest fidelity — merged + correlated) ──
        uf_modules: set[str] = set()
        source_map: dict[str, list[str]] = {}
        if unified_edits and pred_ts_ms > 0:
            uf_modules, source_map = _get_unified_modules_in_window(
                unified_edits, pred_ts_ms,
            )

        # ── TIER 2: copilot_edits (real-time, timestamp windowed) ──
        ce_modules: set[str] = set()
        if not uf_modules and pred_ts_ms > 0 and copilot_edits:
            ce_modules = _get_copilot_edit_modules_in_window(
                copilot_edits, pred_ts_ms,
            )

        # ── TIER 3: edit_pairs (session_n windowed, pulse-based) ──
        ep_modules: set[str] = set()
        matching_edits: list[dict[str, Any]] = []
        if max_session_n >= pred_sn + 2:
            ep_modules, matching_edits = _get_edit_session_modules(
                edit_pairs, pred_sn, EVAL_WINDOW,
            )

        # Merge all tiers — unified is superset, others fill gaps
        actual_modules = uf_modules | ce_modules | ep_modules
        if not actual_modules:
            continue

        journal_window = _load_journal_window(root, pred_sn, EVAL_WINDOW)
        rework_signal = _get_rework_in_window(rework_entries, journal_window)

        result = score_prediction(pred, actual_modules, matching_edits, rework_signal)
        # Tag source breakdown for diagnostics
        result["source_breakdown"] = {
            "unified_modules": sorted(uf_modules),
            "copilot_edits_modules": sorted(ce_modules),
            "edit_pairs_modules": sorted(ep_modules),
            "edit_sources": {k: list(set(v)) for k, v in source_map.items()},
        }
        scored_results.append(result)
        newly_scored_ids.add(pred.get("prediction_id"))

    if not scored_results:
        return {"status": "no_scorable", "scored": 0}

    # Mark predictions as scored
    for pred in predictions:
        if pred.get("prediction_id") in newly_scored_ids:
            pred["scored"] = True
    save_predictions(root, predictions)

    # Backfill into node memory
    nodes_updated = backfill_prediction_scores(root, scored_results)

    # Update calibration
    cal = _update_calibration(root, scored_results)

    # Persist scored results
    existing = _load_scores(root)
    existing.extend(scored_results)
    _save_scores(root, existing)

    combineds = [s["score"]["combined"] for s in scored_results]
    avg_combined = sum(combineds) / len(combineds) if combineds else 0.0

    return {
        "status": "scored",
        "predictions_scored": len(scored_results),
        "avg_combined": round(avg_combined, 3),
        "avg_f1": round(
            sum(s["score"]["f1"] for s in scored_results) / len(scored_results), 3
        ),
        "nodes_updated": nodes_updated,
        "overconfidence_rate": cal.get("overconfidence_rate", 0.0),
        "edits_available": len(edit_pairs),
        "copilot_edits_available": len(copilot_edits),
        "unified_edits_available": len(unified_edits),
    }


def score_predictions_post_commit(root: Path) -> dict[str, Any]:
    """Secondary audit: score against git diff HEAD~1 + copilot_edits (delayed confirmation).

    Supplements edit-session scoring with commit-level ground truth,
    merged with real-time copilot edit data.
    """
    from .预p_pr_s009_v004_d0330_踪稿析_λρ import (
        load_predictions,
    )

    predictions = load_predictions(root)
    if not predictions:
        return {"status": "no_predictions", "scored": 0}

    # Source 1: git diff
    git_modules: set[str] = set()
    changed: list[str] = []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode == 0:
            changed = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
            git_modules = {extract_module_name(f) for f in changed}
            git_modules.discard(None)
    except Exception:
        pass

    # Source 2: copilot_edits (last 30 min — covers the pre-commit editing session)
    copilot_edits = _load_copilot_edits(root)
    ce_modules: set[str] = set()
    if copilot_edits:
        now_ms = datetime.now(timezone.utc).timestamp() * 1000
        ce_modules = _get_copilot_edit_modules_in_window(
            copilot_edits, now_ms - 1_800_000, 1_800_000,
        )

    actual_modules = git_modules | ce_modules
    if not actual_modules:
        return {"status": "no_diff", "scored": 0}

    rework_entries = _load_rework_log(root)
    rework_signal = {"avg_rework": 0.0, "miss_rate": 0.0, "n_matched": 0}
    if rework_entries:
        scores = [r.get("rework_score", 0.0) for r in rework_entries[-10:]]
        rework_signal["avg_rework"] = sum(scores) / len(scores) if scores else 0.0

    scored = [score_prediction(p, actual_modules, [], rework_signal) for p in predictions]
    nodes_updated = backfill_prediction_scores(root, scored)

    existing = _load_scores(root)
    existing.extend(scored)
    _save_scores(root, existing)

    f1s = [s["score"]["f1"] for s in scored]
    avg_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return {
        "status": "scored",
        "predictions_scored": len(scored),
        "avg_f1": round(avg_f1, 3),
        "nodes_updated": nodes_updated,
        "changed_files": len(changed),
        "actual_modules": sorted(actual_modules)[:15],
        "source_breakdown": {
            "git_diff_modules": len(git_modules),
            "copilot_edits_modules": len(ce_modules),
            "merged_total": len(actual_modules),
        },
    }
