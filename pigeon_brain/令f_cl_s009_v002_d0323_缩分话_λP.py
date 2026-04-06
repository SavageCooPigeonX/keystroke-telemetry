"""CLI entry point for Pigeon Brain — build graph, run observer, export for UI."""


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
        from .图p_ge_s003_v003_d0324_读唤任_λχ import build_graph, graph_stats
        g = build_graph(root)
        cache = root / "pigeon_brain" / "graph_cache.json"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(g, indent=2), encoding="utf-8")
        s = graph_stats(g)
        print(f"Graph built: {s['total_nodes']} nodes, {s['total_edges']} edges")
        for b in s.get("bottlenecks", [])[:5]:
            print(f"  bottleneck: {b['name']} (in_degree={b['in_degree']})")

    elif args.command == "observe":
        from .观f_os_s007_v003_d0401_读谱建册_λA import synthesize_observation, write_agent_coaching
        obs = synthesize_observation(root)
        out = write_agent_coaching(root, obs)
        print(f"Observation written to {out}")
        d = obs.get("deaths", {})
        print(f"Deaths: {d.get('total_deaths', 0)} | "
              f"Dual hotspots: {len(obs.get('dual_substrate_hotspots', []))}")

    elif args.command == "dual":
        from .双f_dsb_s008_v002_d0323_缩分话_λP import render_dual_json
        out = render_dual_json(root)
        print(f"Dual view exported to {out}")

    elif args.command == "stats":
        from .图p_ge_s003_v003_d0324_读唤任_λχ import load_graph, graph_stats
        from .描p_ghm_s004_v002_d0323_缩环检意_λP import load_graph_heat
        from .缩p_fdt_s006_v002_d0323_描环检意_λP import load_death_stats
        from .环检p_ld_s005_v002_d0323_缩描意_λP import load_loop_stats
        g = graph_stats(load_graph(root))
        print(json.dumps({"graph": g, "heat": load_graph_heat(root),
                          "deaths": load_death_stats(root),
                          "loops": load_loop_stats(root)}, indent=2))

    elif args.command == "simulate":
        from .仿f_dsm_s010_v002_d0323_缩分话_λP import run_simulation
        run_simulation(root, n_electrons=args.electrons)

    elif args.command == "live":
        from .服f_ls_s012_v004_d0324_踪稿析_λδ import serve_live
        serve_live(root, ws_port=args.ws_port, http_port=args.http_port)

    elif args.command == "trace":
        from .跑f_tr_s013_v002_d0323_缩分话_λP import run_traced
        run_traced(args.script, root)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
