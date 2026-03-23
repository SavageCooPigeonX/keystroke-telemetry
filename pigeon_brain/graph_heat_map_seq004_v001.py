# @pigeon: seq=004 | role=graph_heat_map | depends=[models,graph_extractor] | exports=[update_graph_heat,load_graph_heat] | tokens=~500
"""Graph heat map — failure accumulator per node. Port of file_heat_map.

Cross-references electron deaths with graph nodes to build a failure
debt map: which nodes consistently kill electrons, cause loops, or
produce timeouts. Isomorphic to file_heat_map but for agent execution.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HEAT_STORE = "graph_heat_map.json"
HIGH_DEATH_THRESH = 3
HIGH_LATENCY_THRESH = 0.5


def update_graph_heat(root: Path, node_name: str, event_type: str,
                      death_cause: str = "", latency_ms: int = 0,
                      job_id: str = "") -> None:
    """Record an execution event against a graph node's heat profile."""
    heat_path = root / HEAT_STORE
    try:
        heat = json.loads(heat_path.read_text("utf-8")) if heat_path.exists() else {}
    except Exception:
        heat = {}

    entry = heat.setdefault(node_name, {
        "samples": [], "total_calls": 0, "total_deaths": 0,
        "total_loops": 0, "avg_latency_ms": 0, "death_causes": {},
    })

    sample = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "latency_ms": latency_ms,
        "job_id": job_id,
    }
    if death_cause:
        sample["death_cause"] = death_cause

    entry["samples"].append(sample)
    entry["samples"] = entry["samples"][-50:]  # keep last 50

    entry["total_calls"] += 1
    if event_type == "error":
        entry["total_deaths"] += 1
        causes = entry["death_causes"]
        causes[death_cause] = causes.get(death_cause, 0) + 1
    if event_type == "loop":
        entry["total_loops"] += 1

    # Recompute averages
    latencies = [s["latency_ms"] for s in entry["samples"] if s.get("latency_ms")]
    entry["avg_latency_ms"] = round(sum(latencies) / max(len(latencies), 1))

    heat_path.write_text(json.dumps(heat, indent=2), encoding="utf-8")


def load_graph_heat(root: Path) -> dict:
    """Load graph heat map → summary for observer synthesis."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        heat = json.loads(heat_path.read_text("utf-8"))
    except Exception:
        return {}

    # Danger zones: high death count
    danger_nodes = sorted(
        [{"node": name, "deaths": d["total_deaths"],
          "loops": d["total_loops"], "calls": d["total_calls"],
          "death_rate": round(d["total_deaths"] / max(d["total_calls"], 1), 3),
          "top_cause": max(d.get("death_causes", {"none": 0}),
                           key=d.get("death_causes", {"none": 0}).get,
                           default="none")}
         for name, d in heat.items()
         if d["total_deaths"] >= HIGH_DEATH_THRESH],
        key=lambda x: x["deaths"],
        reverse=True
    )

    # Bottleneck nodes: high call count
    hot_nodes = sorted(
        [{"node": name, "calls": d["total_calls"],
          "avg_latency_ms": d["avg_latency_ms"]}
         for name, d in heat.items()],
        key=lambda x: x["calls"],
        reverse=True
    )[:10]

    return {
        "nodes_tracked": len(heat),
        "danger_zones": danger_nodes[:5],
        "hot_nodes": hot_nodes,
        "total_deaths": sum(d["total_deaths"] for d in heat.values()),
        "total_loops": sum(d["total_loops"] for d in heat.values()),
    }
