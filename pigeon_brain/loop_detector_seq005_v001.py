# @pigeon: seq=005 | role=loop_detector | depends=[models] | exports=[detect_loops,load_loop_stats] | tokens=~400
"""Loop detector — recurring path detection. Port of query_memory.

Tracks execution paths that recur: the same sequence of file transitions
happening repeatedly = the agent is stuck. Like query_memory fingerprints
recurring questions, this fingerprints recurring execution paths.
"""

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LOOP_STORE = "loop_detector.json"
MAX_ENTRIES = 500
RECUR_THRESH = 3


def _path_fingerprint(path: list[str]) -> str:
    """Stable fingerprint for an execution path."""
    # Strip version info, keep module names
    clean = [re.sub(r'_seq\d+.*$', '', f).strip() for f in path]
    return " → ".join(clean[-6:])  # last 6 hops


def record_path(root: Path, job_id: str, path: list[str],
                status: str, death_cause: str = "") -> None:
    """Record a completed electron path for loop analysis."""
    store_path = root / LOOP_STORE
    try:
        store = json.loads(store_path.read_text("utf-8")) if store_path.exists() else {}
    except Exception:
        store = {}

    paths = store.get("paths", [])
    loops = store.get("detected_loops", [])

    fp = _path_fingerprint(path)
    paths.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "fingerprint": fp,
        "length": len(path),
        "status": status,
        "death_cause": death_cause,
    })

    # Check for within-path loops (node visited 3+ times)
    node_counts = Counter(path)
    internal_loops = [
        {"node": node, "visits": count}
        for node, count in node_counts.items()
        if count >= RECUR_THRESH
    ]
    if internal_loops:
        loops.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "loops": internal_loops,
            "path_length": len(path),
        })

    store["paths"] = paths[-MAX_ENTRIES:]
    store["detected_loops"] = loops[-MAX_ENTRIES:]
    store_path.write_text(json.dumps(store, indent=2), encoding="utf-8")


def load_loop_stats(root: Path) -> dict:
    """Aggregate loop data → summary for observer synthesis."""
    store_path = root / LOOP_STORE
    if not store_path.exists():
        return {}
    try:
        store = json.loads(store_path.read_text("utf-8"))
    except Exception:
        return {}

    paths = store.get("paths", [])
    loops = store.get("detected_loops", [])

    # Find recurring path fingerprints (same path taken 3+ times)
    fps = [p["fingerprint"] for p in paths]
    counts = Counter(fps)
    recurring = [
        {"path": fp, "count": cnt,
         "last_status": next((p["status"] for p in reversed(paths)
                              if p["fingerprint"] == fp), "unknown")}
        for fp, cnt in counts.most_common(5)
        if cnt >= RECUR_THRESH
    ]

    # Most-looped nodes across all detected internal loops
    all_loop_nodes = Counter()
    for entry in loops:
        for lp in entry.get("loops", []):
            all_loop_nodes[lp["node"]] += lp["visits"]
    worst_loop_nodes = [
        {"node": n, "total_revisits": c}
        for n, c in all_loop_nodes.most_common(5)
    ]

    dead_paths = sum(1 for p in paths if p["status"] == "dead")

    return {
        "total_paths": len(paths),
        "recurring_paths": recurring,
        "internal_loops": len(loops),
        "worst_loop_nodes": worst_loop_nodes,
        "dead_path_count": dead_paths,
        "dead_path_rate": round(dead_paths / max(len(paths), 1), 3),
    }
