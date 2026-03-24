# @pigeon: seq=010 | role=demo_simulation | depends=[execution_logger,graph_extractor,failure_detector,loop_detector,graph_heat_map] | exports=[run_simulation] | tokens=~550
"""Demo simulation — generates execution telemetry from the real graph.

Takes the pigeon_registry graph and simulates electrons flowing through it,
with realistic failure patterns: stale imports, timeouts, loops.
Produces real telemetry files that the UI can render.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v002 | 126 lines | ~1,358 tokens
# DESC:   generates_execution_telemetry_from_the
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

import random
import time
from pathlib import Path

from .execution_logger_seq002_v002_d0323__isomorphic_to_telemetrylogger_for_agent_lc_pigeon_brain_system import ExecutionLogger
from .graph_extractor_seq003_v003_d0324__extract_the_cognition_graph_from_lc_gemini_chat_dead import build_graph
from .graph_heat_map_seq004_v002_d0323__failure_accumulator_per_node_port_lc_pigeon_brain_system import update_graph_heat
from .loop_detector_seq005_v002_d0323__recurring_path_detection_port_of_lc_pigeon_brain_system import record_path
from .failure_detector_seq006_v002_d0323__electron_death_classification_port_of_lc_pigeon_brain_system import classify_death, record_death


# Nodes that are realistically "dangerous" in pigeon codebases
DANGER_PATTERNS = ["self_fix", "import_rewriter", "deepseek_adapter",
                   "run_clean_split", "cognitive_reactor"]
DEATH_CAUSES = ["exception", "timeout", "loop", "stale_import", "max_attempts"]


def run_simulation(root: Path, n_electrons: int = 10) -> dict:
    """Simulate n electrons flowing through the real graph."""
    graph = build_graph(root)
    nodes = list(graph.get("nodes", {}).keys())
    if not nodes:
        print("No graph nodes found. Run 'py -m pigeon_brain graph' first.")
        return {}

    logger = ExecutionLogger(log_dir=str(root / "logs" / "execution"),
                             live_print=True)
    results = {"total": n_electrons, "complete": 0, "dead": 0, "paths": []}

    print(f"\n{'='*70}")
    print(f"  PIGEON BRAIN SIMULATION — {n_electrons} electrons")
    print(f"  Graph: {len(nodes)} nodes")
    print(f"{'='*70}\n")

    for i in range(n_electrons):
        # Pick a random starting node
        start = random.choice(nodes)
        path_length = random.randint(3, min(12, len(nodes)))
        job_id = logger.start_electron(context={"electron": i + 1,
                                                "start": start})

        path = [start]
        current = start
        alive = True

        print(f"  ⚡ Electron {i+1}/{n_electrons} born at {start}")

        for step in range(path_length):
            # Pick next node: prefer edges_out if they exist
            node_data = graph["nodes"].get(current, {})
            edges_out = node_data.get("edges_out", [])
            # 70% follow real edges, 30% random jump
            if edges_out and random.random() < 0.7:
                next_node = random.choice(edges_out)
            else:
                next_node = random.choice(nodes)

            logger.log_call(current, next_node, job_id,
                            context={"step": step + 1})
            update_graph_heat(root, next_node, "call", job_id=job_id)
            path.append(next_node)

            # Death check: danger nodes have higher kill probability
            is_danger = any(p in next_node for p in DANGER_PATTERNS)
            death_prob = 0.15 if is_danger else 0.03

            if random.random() < death_prob:
                cause = random.choice(DEATH_CAUSES)
                if is_danger:
                    cause = random.choice(["stale_import", "exception", "timeout"])
                logger.log_error(next_node, job_id, f"simulated {cause}",
                                 cause=cause)
                update_graph_heat(root, next_node, "error",
                                  death_cause=cause, job_id=job_id)

                electron = logger.electrons[job_id]
                electron.path = path
                c = classify_death({
                    "status": "dead", "death_cause": cause,
                    "path": path, "loop_count": electron.loop_count,
                    "total_errors": electron.total_errors,
                    "total_calls": electron.total_calls,
                })
                record_death(root, c, job_id)
                record_path(root, job_id, path, "dead", cause)

                sym = {"exception": "💥", "timeout": "⏱️",
                       "loop": "🔄", "stale_import": "⚡",
                       "max_attempts": "🔴"}.get(cause, "💀")
                print(f"    {sym} DEAD at {next_node} ({cause}) "
                      f"after {step+1} hops")
                results["dead"] += 1
                alive = False
                break

            current = next_node

        if alive:
            logger.complete_electron(job_id)
            logger.electrons[job_id].path = path
            record_path(root, job_id, path, "complete")
            print(f"    ✅ Complete — {len(path)} hops")
            results["complete"] += 1

        results["paths"].append({"job_id": job_id, "path": path,
                                 "alive": alive})

    summary = logger.write_summary()
    logger.close()

    print(f"\n{'='*70}")
    print(f"  Results: {results['complete']} complete, "
          f"{results['dead']} dead / {n_electrons} total")
    print(f"  Logs: {logger.events_file}")
    print(f"  Summary: {logger.summary_file}")
    print(f"{'='*70}\n")

    return results
