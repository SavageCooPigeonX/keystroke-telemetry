"""描p_ghm_s004_v002_d0323_缩环检意_λP_load_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 44 lines | ~389 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

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
