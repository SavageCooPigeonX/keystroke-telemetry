"""双f_dsb_s008_v002_d0323_缩分话_λP_orchestrator_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 89 lines | ~835 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .图p_ge_s003_v003_d0324_读唤任_λχ import load_graph
from datetime import datetime, timezone
from pathlib import Path

def build_dual_view(root: Path) -> dict:
    """Build unified node data with both human and agent heat.

    Returns {nodes: [{name, human_heat, agent_heat, dual_score, ...}]}
    """
    graph = load_graph(root)
    agent_heat = _load_agent_heat_raw(root)
    human_heat = _load_human_heat_raw(root)
    profiles = _load_file_profiles(root)

    nodes = []
    for name, node in graph.get("nodes", {}).items():
        human_hes = human_heat.get(name, {}).get("avg_hes", 0.0)
        human_miss = human_heat.get(name, {}).get("miss_count", 0)

        agent_deaths = 0
        agent_calls = 0
        agent_latency = 0
        agent_loops = 0
        last_called = None
        death_causes = {}
        ah = agent_heat.get(name, {}) if isinstance(agent_heat, dict) else {}
        if isinstance(ah, dict) and "total_deaths" in ah:
            agent_deaths = ah.get("total_deaths", 0)
            agent_calls = ah.get("total_calls", 0)
            agent_latency = ah.get("avg_latency_ms", 0)
            agent_loops = ah.get("total_loops", 0)
            death_causes = ah.get("death_causes", {})
            samples = ah.get("samples", [])
            if samples:
                last_called = samples[-1].get("ts", None)

        # Dual score: combined human + agent danger
        dual_score = round(
            human_hes * 0.4 +
            min(agent_deaths / max(agent_calls, 1), 1.0) * 0.4 +
            (human_miss > 0) * 0.1 +
            (agent_deaths > 0) * 0.1,
            3
        )

        # File profile data
        prof = profiles.get(name, {})
        death_rate = round(agent_deaths / max(agent_calls, 1), 3)

        nodes.append({
            "name": name,
            "desc": node.get("desc", ""),
            "path": node.get("path", ""),
            "seq": node.get("seq", 0),
            "ver": node.get("ver", 1),
            "tokens": node.get("tokens", 0),
            "lines": _count_lines(root, node.get("path", "")),
            "edges_out": node.get("edges_out", []),
            "edges_in": node.get("edges_in", []),
            "in_degree": len(node.get("edges_in", [])),
            "out_degree": len(node.get("edges_out", [])),
            # Human substrate
            "human_hesitation": round(human_hes, 3),
            "human_misses": human_miss,
            # Agent substrate
            "agent_deaths": agent_deaths,
            "agent_calls": agent_calls,
            "agent_latency_ms": agent_latency,
            "agent_loops": agent_loops,
            "death_rate": death_rate,
            "death_causes": death_causes,
            "last_called": last_called,
            # Profile
            "personality": prof.get("personality", "unknown"),
            "fears": prof.get("fears", []),
            "partners": [p["name"] for p in prof.get("partners", [])[:3]],
            # Combined
            "dual_score": dual_score,
        })

    nodes.sort(key=lambda x: x["dual_score"], reverse=True)

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "total_nodes": len(nodes),
        "nodes": nodes,
        "edges": graph.get("edges", []),
    }
