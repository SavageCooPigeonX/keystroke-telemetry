# @pigeon: seq=006 | role=failure_detector | depends=[models,graph_heat_map,loop_detector] | exports=[classify_death,record_death,load_death_stats] | tokens=~450
"""Failure detector — electron death classification. Port of rework_detector.

Classifies why an electron died (exception, timeout, loop, stale_import, max_attempts)
and accumulates per-session death stats. Like rework_detector scores human intent
deaths as miss/partial/ok, this scores agent intent deaths by cause.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DEATH_STORE = "execution_death_log.json"
MAX_ENTRIES = 200

STALL_MS = 10_000
TIMEOUT_MS = 30_000


def classify_death(electron: dict) -> dict:
    """Classify an electron's death from its lifecycle data.

    Returns {cause, severity, node, score, detail}
    """
    status = electron.get("status", "")
    death_cause = electron.get("death_cause", "")
    path = electron.get("path", [])
    loop_count = electron.get("loop_count", 0)
    total_errors = electron.get("total_errors", 0)
    total_calls = electron.get("total_calls", 0)

    # Determine node where death occurred
    death_node = path[-1] if path else "unknown"

    if death_cause == "stale_import":
        severity = "critical"
        score = 0.9
        detail = f"Stale import killed electron at {death_node}"
    elif death_cause == "timeout":
        severity = "high"
        score = 0.7
        detail = f"Timeout after {total_calls} calls at {death_node}"
    elif loop_count > 0:
        severity = "high"
        score = 0.65
        detail = f"Loop detected: {loop_count} revisits, died at {death_node}"
    elif death_cause == "max_attempts":
        severity = "medium"
        score = 0.5
        detail = f"Max attempts reached at {death_node}"
    elif death_cause == "exception":
        severity = "high"
        score = 0.75
        detail = f"Exception at {death_node} after {total_calls} calls"
    else:
        severity = "low"
        score = 0.3
        detail = f"Unknown death at {death_node}"

    return {
        "cause": death_cause or "unknown",
        "severity": severity,
        "node": death_node,
        "score": score,
        "detail": detail,
        "path_length": len(path),
    }


def record_death(root: Path, classification: dict, job_id: str) -> None:
    """Append a death event to execution_death_log.json."""
    log_path = root / DEATH_STORE
    try:
        existing = json.loads(log_path.read_text("utf-8")) if log_path.exists() else []
    except Exception:
        existing = []

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        **classification,
    }
    existing.append(entry)
    log_path.write_text(json.dumps(existing[-MAX_ENTRIES:], indent=2),
                        encoding="utf-8")


def load_death_stats(root: Path) -> dict:
    """Aggregate death log → summary for observer synthesis."""
    log_path = root / DEATH_STORE
    if not log_path.exists():
        return {}
    try:
        events = json.loads(log_path.read_text("utf-8"))
    except Exception:
        return {}
    if not events:
        return {}

    total = len(events)
    by_cause = {}
    by_node = {}
    for e in events:
        cause = e.get("cause", "unknown")
        by_cause[cause] = by_cause.get(cause, 0) + 1
        node = e.get("node", "unknown")
        by_node[node] = by_node.get(node, 0) + 1

    # Most lethal nodes
    worst_nodes = sorted(by_node.items(), key=lambda x: x[1], reverse=True)[:5]
    scores = [e.get("score", 0) for e in events]
    avg_score = round(sum(scores) / len(scores), 3)

    # Critical deaths (stale_import, exception, timeout)
    critical = sum(1 for e in events if e.get("severity") in ("critical", "high"))

    return {
        "total_deaths": total,
        "by_cause": by_cause,
        "worst_nodes": [{"node": n, "deaths": c} for n, c in worst_nodes],
        "avg_death_score": avg_score,
        "critical_count": critical,
        "critical_rate": round(critical / max(total, 1), 3),
    }
