# @pigeon: seq=007 | role=observer_synthesis | depends=[graph_heat_map,loop_detector,failure_detector,graph_extractor] | exports=[synthesize_observation,build_observer_prompt] | tokens=~550
"""Observer synthesis — coaching from execution patterns. Port of classify_bridge.

Aggregates graph heat, loop detection, and death stats into a structured
observation that either feeds a DeepSeek prompt or writes agent_coaching.md.
Isomorphic to operator coaching synthesis but for agent execution substrate.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v003 | 150 lines | ~1,489 tokens
# DESC:   coaching_from_execution_patterns_port
# INTENT: add_chinese_glyph
# LAST:   2026-04-01 @ aa32a3f
# SESSIONS: 2
# ──────────────────────────────────────────────

import json
from datetime import datetime, timezone
from pathlib import Path

from .graph_heat_map_seq004_v002_d0323__failure_accumulator_per_node_port_lc_pigeon_brain_system import load_graph_heat
from .loop_detector_seq005_v002_d0323__recurring_path_detection_port_of_lc_pigeon_brain_system import load_loop_stats
from .failure_detector_seq006_v002_d0323__electron_death_classification_port_of_lc_pigeon_brain_system import load_death_stats
from .graph_extractor_seq003_v003_d0324__图_extract_the_cognition_graph_from_lc_gemini_chat_dead import load_graph, graph_stats

COACHING_PATH = "agent_coaching.md"


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


def build_observer_prompt(observation: dict) -> str:
    """Build a prompt for DeepSeek from observation data.

    Same structure as _build_commit_coaching_prompt in git_plugin
    but targeting execution domain.
    """
    sections = []
    sections.append("# Agent Execution Observation Report\n")

    # Graph stats
    g = observation.get("graph", {})
    sections.append(f"## Graph: {g.get('total_nodes', 0)} nodes, "
                    f"{g.get('total_edges', 0)} edges\n")
    for b in g.get("bottlenecks", [])[:3]:
        sections.append(f"- Bottleneck: **{b['name']}** "
                        f"(in_degree={b['in_degree']})")

    # Death summary
    d = observation.get("deaths", {})
    if d:
        sections.append(f"\n## Deaths: {d.get('total_deaths', 0)} total, "
                        f"{d.get('critical_rate', 0):.0%} critical")
        for node in d.get("worst_nodes", [])[:3]:
            sections.append(f"- **{node['node']}**: {node['deaths']} deaths")
        by_cause = d.get("by_cause", {})
        if by_cause:
            sections.append(f"- Causes: {by_cause}")

    # Loop summary
    lp = observation.get("loops", {})
    if lp and lp.get("recurring_paths"):
        sections.append(f"\n## Loops: {lp.get('internal_loops', 0)} detected")
        for rp in lp.get("recurring_paths", [])[:3]:
            sections.append(f"- `{rp['path']}` — {rp['count']}x "
                            f"(last: {rp['last_status']})")

    # Heat zones
    h = observation.get("heat", {})
    if h and h.get("danger_zones"):
        sections.append(f"\n## Danger Zones")
        for dz in h.get("danger_zones", [])[:3]:
            sections.append(f"- **{dz['node']}**: {dz['deaths']} deaths, "
                            f"death_rate={dz['death_rate']:.0%}, "
                            f"top_cause={dz['top_cause']}")

    # Dual-substrate hotspots (the killer feature)
    dual = observation.get("dual_substrate_hotspots", [])
    if dual:
        sections.append(f"\n## DUAL-SUBSTRATE HOTSPOTS (human + agent failures)")
        for ds in dual:
            sections.append(
                f"- **{ds['node']}**: human_hesitation={ds['human_hesitation']:.3f}, "
                f"electron_deaths={ds['electron_deaths']} — "
                f"DECOMPOSE IMMEDIATELY"
            )

    sections.append("\n---\nGenerate 3-5 specific actions to reduce deaths.")
    return "\n".join(sections)


def _load_human_heat(root: Path) -> dict:
    """Load the human file_heat_map for dual-substrate comparison."""
    heat_path = root / "file_heat_map.json"
    if not heat_path.exists():
        return {}
    try:
        import importlib.util as ilu
        import glob
        matches = sorted(glob.glob(str(root / "src" / "热p_fhm_s011*.py")))
        if not matches:
            return {}
        spec = ilu.spec_from_file_location("_fhm", matches[-1])
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.load_heat_map(root)
    except Exception:
        return {}


def write_agent_coaching(root: Path, observation: dict) -> Path:
    """Write agent_coaching.md from observation — like operator_coaching.md."""
    prompt = build_observer_prompt(observation)
    out = root / COACHING_PATH
    out.write_text(prompt, encoding="utf-8")
    return out
