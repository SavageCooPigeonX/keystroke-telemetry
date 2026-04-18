"""观f_os_s007_v003_d0401_读谱建册_λA_synthesize_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 43 lines | ~414 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .图p_ge_s003_v003_d0324_读唤任_λχ import load_graph, graph_stats
from .描p_ghm_s004_v002_d0323_缩环检意_λP import load_graph_heat
from .环检p_ld_s005_v002_d0323_缩描意_λP import load_loop_stats
from .缩p_fdt_s006_v002_d0323_描环检意_λP import load_death_stats
from datetime import datetime, timezone
from pathlib import Path

def synthesize_observation(root: Path) -> dict:
    """Aggregate all execution telemetry into a single observation."""
    heat = load_graph_heat(root)
    loops = load_loop_stats(root)
    deaths = load_death_stats(root)
    graph = load_graph(root)
    stats = graph_stats(graph)

    # Build dual-substrate comparison if human telemetry exists
    human_heat = _load_human_heat(root)

    # Find nodes that kill BOTH humans and electrons
    dual_deaths = []
    if human_heat and heat:
        danger_nodes = {d["node"] for d in heat.get("danger_zones", [])}
        for hf in human_heat.get("complex_files", []):
            mod = hf.get("module", "")
            if mod in danger_nodes:
                dual_deaths.append({
                    "node": mod,
                    "human_hesitation": hf.get("avg_hes", 0),
                    "electron_deaths": next(
                        (d["deaths"] for d in heat["danger_zones"]
                         if d["node"] == mod), 0
                    ),
                })

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "graph": stats,
        "heat": heat,
        "loops": loops,
        "deaths": deaths,
        "dual_substrate_hotspots": dual_deaths,
    }
