# @pigeon: seq=009 | role=cli | depends=[*] | exports=[main] | tokens=~350
"""CLI entry point for Pigeon Brain — build graph, run observer, export for UI."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v002 | 81 lines | ~1,016 tokens
# DESC:   build_graph_run_observer_export
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Pigeon Brain — dual-substrate observation")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("graph", help="Build/rebuild the cognition graph")
    sub.add_parser("observe", help="Run observer synthesis")
    sub.add_parser("dual", help="Export dual-substrate view for UI")
    sub.add_parser("stats", help="Print graph + execution stats")
    sim = sub.add_parser("simulate", help="Run a demo simulation")
    sim.add_argument("--electrons", type=int, default=10)
    live = sub.add_parser("live", help="Start live trace server (WebSocket + HTTP)")
    live.add_argument("--ws-port", type=int, default=8765)
    live.add_argument("--http-port", type=int, default=8766)
    trace = sub.add_parser("trace", help="Run a script with execution tracing")
    trace.add_argument("script", help="Path to Python script to trace")

    args = parser.parse_args()
    root = Path(".")

    if args.command == "graph":
        from .graph_extractor_seq003_v003_d0324__extract_the_cognition_graph_from_lc_gemini_chat_dead import build_graph, graph_stats
        g = build_graph(root)
        cache = root / "pigeon_brain" / "graph_cache.json"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(g, indent=2), encoding="utf-8")
        s = graph_stats(g)
        print(f"Graph built: {s['total_nodes']} nodes, {s['total_edges']} edges")
        for b in s.get("bottlenecks", [])[:5]:
            print(f"  bottleneck: {b['name']} (in_degree={b['in_degree']})")

    elif args.command == "observe":
        from .observer_synthesis_seq007_v002_d0323__coaching_from_execution_patterns_port_lc_pigeon_brain_system import synthesize_observation, write_agent_coaching
        obs = synthesize_observation(root)
        out = write_agent_coaching(root, obs)
        print(f"Observation written to {out}")
        d = obs.get("deaths", {})
        print(f"Deaths: {d.get('total_deaths', 0)} | "
              f"Dual hotspots: {len(obs.get('dual_substrate_hotspots', []))}")

    elif args.command == "dual":
        from .dual_substrate_seq008_v002_d0323__merges_human_and_agent_telemetry_lc_pigeon_brain_system import render_dual_json
        out = render_dual_json(root)
        print(f"Dual view exported to {out}")

    elif args.command == "stats":
        from .graph_extractor_seq003_v003_d0324__extract_the_cognition_graph_from_lc_gemini_chat_dead import load_graph, graph_stats
        from .graph_heat_map_seq004_v002_d0323__failure_accumulator_per_node_port_lc_pigeon_brain_system import load_graph_heat
        from .failure_detector_seq006_v002_d0323__electron_death_classification_port_of_lc_pigeon_brain_system import load_death_stats
        from .loop_detector_seq005_v002_d0323__recurring_path_detection_port_of_lc_pigeon_brain_system import load_loop_stats
        g = graph_stats(load_graph(root))
        print(json.dumps({"graph": g, "heat": load_graph_heat(root),
                          "deaths": load_death_stats(root),
                          "loops": load_loop_stats(root)}, indent=2))

    elif args.command == "simulate":
        from .demo_sim_seq010_v002_d0323__generates_execution_telemetry_from_the_lc_pigeon_brain_system import run_simulation
        run_simulation(root, n_electrons=args.electrons)

    elif args.command == "live":
        from .live_server_seq012_v004_d0324__websocket_server_for_live_execution_lc_per_prompt_deleted import serve_live
        serve_live(root, ws_port=args.ws_port, http_port=args.http_port)

    elif args.command == "trace":
        from .traced_runner_seq013_v002_d0323__run_any_python_script_with_lc_pigeon_brain_system import run_traced
        run_traced(args.script, root)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
