# ┌───────────────────────────────────────────────┐
# │  flow_engine — routes packets through the graph │
# │  pigeon_brain/flow                              │
# └───────────────────────────────────────────────┘
"""
The flow engine is the runtime.

Given a task seed, it:
  1. Finds an origin node (or accepts one explicitly)
  2. Creates a context packet
  3. Wakes the origin node
  4. Asks the path selector for the next node
  5. Transports the packet along the edge (vein effects)
  6. Wakes the next node
  7. Repeats until the path terminates or the packet dies
  8. Returns the completed packet for task writing

For multi-perspective reasoning, run_multi() launches packets
through all 3 modes and returns all results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .包p_cpk_s001_v002_d0324_缩分话_λε import ContextPacket, create_packet
from .唤w_noaw_s002_v003_d0401_脉运分话_λA import awaken
from .择p_pase_s004_v002_d0324_分话唤_λε import find_origin, select_next
from .脉运w_vt_s006_v003_d0401_唤分话_λA import transport


def load_graph_data(root: Path) -> dict[str, Any]:
    """Load and merge all graph intelligence sources."""
    data: dict[str, Any] = {"nodes": {}}

    # 1. Base graph topology
    graph_path = root / "pigeon_brain" / "graph_cache.json"
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        data["nodes"] = graph.get("nodes", {})

    # 2. Merge dual-substrate enrichment
    dual_path = root / "pigeon_brain" / "dual_view.json"
    if dual_path.exists():
        dual = json.loads(dual_path.read_text(encoding="utf-8"))
        for enriched in dual.get("nodes", []):
            name = enriched.get("name", "")
            if name in data["nodes"]:
                data["nodes"][name].update(enriched)
            else:
                data["nodes"][name] = enriched

    # 3. Merge vein/clot data onto nodes
    veins_path = root / "pigeon_brain" / "context_veins_seq001_v001.json"
    veins_data = None
    if veins_path.exists():
        veins_data = json.loads(veins_path.read_text(encoding="utf-8"))
        _merge_veins(data["nodes"], veins_data)

    data["_veins"] = veins_data
    return data


def _merge_veins(nodes: dict, veins_data: dict) -> None:
    """Overlay vein/clot signals onto graph nodes."""
    for entry in veins_data.get("clots", []):
        name = entry.get("module", "")
        if name in nodes:
            nodes[name]["clot_signals"] = entry.get("clot_signals", [])
            nodes[name]["vein_score"] = entry.get("vein_score", 0.0)
    for entry in veins_data.get("arteries", []):
        name = entry.get("module", "")
        if name in nodes:
            nodes[name]["vein_score"] = entry.get("vein_score", 1.0)


def run_flow(
    root: Path,
    task_seed: str,
    mode: str = "targeted",
    origin: str | None = None,
    graph_data: dict[str, Any] | None = None,
) -> ContextPacket:
    """
    Run a single packet through the graph.

    Args:
        root: project root
        task_seed: the bug/task/question text
        mode: "targeted" | "heat" | "failure"
        origin: explicit start node (auto-detected if None)
        graph_data: pre-loaded graph (loaded if None)

    Returns:
        The completed ContextPacket with accumulated intelligence.
    """
    if graph_data is None:
        graph_data = load_graph_data(root)

    # Find origin
    if origin is None:
        origin = find_origin(task_seed, graph_data)
    if origin is None:
        # Fallback: pick highest-heat node
        nodes = graph_data.get("nodes", {})
        if nodes:
            origin = max(nodes, key=lambda n: nodes[n].get("dual_score", 0))
        else:
            packet = create_packet("unknown", task_seed, mode)
            packet.alive = False
            return packet

    packet = create_packet(origin, task_seed, mode)
    veins_data = graph_data.get("_veins")

    # Wake origin node
    awaken(origin, packet, graph_data)

    # Flow through the graph
    current = origin
    while packet.alive:
        visited = set(packet.path)
        next_node = select_next(
            current, visited, mode, graph_data, packet.depth
        )
        if next_node is None:
            break

        # Transport along the edge (vein effects)
        transport(packet, current, next_node, graph_data, veins_data)

        if not packet.alive:
            break

        # Wake the next node
        awaken(next_node, packet, graph_data)
        current = next_node

    return packet


def run_multi(
    root: Path,
    task_seed: str,
    origin: str | None = None,
) -> list[ContextPacket]:
    """
    Multi-perspective: run the same task through all 3 path modes.

    Returns list of completed packets — one per mode.
    Same graph, different thinking.
    """
    graph_data = load_graph_data(root)

    if origin is None:
        origin = find_origin(task_seed, graph_data)

    results = []
    for mode in ("targeted", "heat", "failure"):
        packet = run_flow(
            root, task_seed, mode=mode,
            origin=origin, graph_data=graph_data,
        )
        results.append(packet)

    return results
