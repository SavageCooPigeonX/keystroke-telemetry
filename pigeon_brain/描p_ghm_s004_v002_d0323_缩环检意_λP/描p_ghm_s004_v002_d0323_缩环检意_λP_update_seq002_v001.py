"""描p_ghm_s004_v002_d0323_缩环检意_λP_update_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 45 lines | ~406 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

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
