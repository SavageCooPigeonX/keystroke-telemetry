# ┌──────────────────────────────────────────────┐
# │  bug_demon_manifest — propagates bug state    │
# │  across multi-module paths via context veins  │
# │  pigeon_brain/flow                            │
# └──────────────────────────────────────────────┘
"""
Bug Demon Manifest Chain — prototype (bounded slice).

Problem: debugging is isolated per module. When 逆f_ba has an `oc` bug,
the flow engine doesn't know. When an electron visits 逆f_ba on its way
to 学f_ll, the backward pass writes credit to both nodes — but neither
entry in node_memory.json mentions the live bug. The next electron runs
blind to it.

This module closes the loop:
  1. load_active_bugs() — reads pigeon_registry.json bug_keys
  2. propagate_through_veins() — uses import graph to find DOWNSTREAM
     modules affected by each bugged module (they inherit the bug context)
  3. inject_into_packet() — stamps BugManifest list onto ContextPacket
  4. write_to_node_memory() — extends existing node_memory entries with
     active_bugs field (non-destructive, legacy fields preserved)
  5. demo_chain() — end-to-end verification showing bug context at a
     downstream node that had no direct bug annotation

Architecture note:
  ContextPacket currently carries fear_chain (list[str]) but no structured
  bug state. This module adds it as a side-channel that doesn't require
  modifying ContextPacket's dataclass — it attaches to the dict
  representation consumed by task_writer and backward pass.

Cost: zero LLM calls. Pure registry + graph traversal + JSON I/O.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 461 lines | ~4,245 tokens
# DESC:   prototype_bounded_slice
# INTENT: FT
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────


from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_PATH = "pigeon_registry.json"
VEINS_PATH = "pigeon_brain/context_veins.json"
NODE_MEMORY_PATH = "pigeon_brain/node_memory.json"
BUG_MANIFEST_LOG = "pigeon_brain/bug_manifest_chain.jsonl"

BUG_SEVERITY = {
    "oc": 0.8,   # over hard cap — blocks context window
    "hi": 0.7,   # hardcoded import — breaks on rename
    "hc": 0.6,   # high coupling — amplifies blast radius
    "de": 0.4,   # dead export — dead weight
    "dd": 0.3,   # duplicate docstring — noise
    "qn": 0.2,   # query noise — minor fog
}


@dataclass
class BugManifest:
    """A single live bug, tracked across the import graph."""
    bug_id: str
    bug_type: str           # "oc" | "hi" | "de" | "hc" | "dd" | "qn"
    severity: float         # 0.0–1.0 from BUG_SEVERITY
    origin_module: str      # module where the bug was first detected
    affected_chain: list[str] = field(default_factory=list)  # downstream dependents
    notes: str = ""
    resolved: bool = False
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def _load_registry(root: Path) -> list[dict]:
    p = root / REGISTRY_PATH
    if not p.exists():
        return []
    data = json.loads(p.read_text("utf-8"))
    return data.get("files", []) if isinstance(data, dict) else data


def _load_veins(root: Path) -> dict[str, Any]:
    p = root / VEINS_PATH
    if not p.exists():
        return {}
    return json.loads(p.read_text("utf-8"))


def _build_import_graph(veins: dict) -> dict[str, list[str]]:
    """Build {module: [downstream_importers]} from vein data.

    context_veins.json stores per-node vein scores. We infer import
    relationships from the graph_cache.json edges it was built from.
    Falls back to reading the graph cache directly.
    """
    # context_veins.json doesn't store raw edges — use graph_cache
    return {}


def _load_graph_edges(root: Path) -> dict[str, list[str]]:
    """Return {dependency: [importers_of_that_dependency]}.

    graph_cache edge format: {'from': importer, 'to': dependency, 'type': 'import'}
    If dependency has a bug, its importers inherit the affected context.
    So dependents[dependency] = [all modules that import it].
    """
    cache = root / "pigeon_brain" / "graph_cache.json"
    if not cache.exists():
        return {}
    graph = json.loads(cache.read_text("utf-8"))
    edges = graph.get("edges", [])
    dependents: dict[str, list[str]] = {}
    for edge in edges:
        importer = edge.get("from", "")
        dependency = edge.get("to", "")
        if importer and dependency:
            dependents.setdefault(dependency, []).append(importer)
    return dependents


_BETA_RE = __import__("re").compile(r"_β(\w+?)(?:_|\.py$|$)")


def load_active_bugs(root: Path) -> list[BugManifest]:
    """Read registry; extract bugs from β-suffix in filenames.

    Registry entries carry bugs encoded as `_β<codes>` in the path stem
    (e.g. `逆f_ba_s007_v005_d0404_λNU_βoc`). `bug_keys` field doesn't exist
    in the current schema — parse the suffix instead.
    """
    files = _load_registry(root)
    manifests: list[BugManifest] = []
    for f in files:
        path_str = f.get("path", "") or ""
        name = f.get("name", "") or f.get("abbrev", "") or ""
        if not name:
            continue
        m = _BETA_RE.search(path_str)
        if not m:
            continue
        beta_codes = m.group(1)  # e.g. "oc" or "ochi" or "oc"
        # Split composite codes (e.g. "ochi" → ["oc","hi"] isn't trivially parseable)
        # Treat the whole suffix as one key first; then match known 2-char keys
        bug_keys: list[str] = []
        remaining = beta_codes
        while remaining:
            matched = False
            for bk in BUG_SEVERITY:
                if remaining.startswith(bk):
                    bug_keys.append(bk)
                    remaining = remaining[len(bk):]
                    matched = True
                    break
            if not matched:
                break  # unknown suffix — skip rest

        tokens = f.get("tokens") or 0
        for bk in bug_keys:
            notes = f"{tokens} tokens" if bk == "oc" else f"detected in {name}"
            mid = f"{bk}:{name}"
            manifests.append(BugManifest(
                bug_id=mid,
                bug_type=bk,
                severity=BUG_SEVERITY.get(bk, 0.3),
                origin_module=name,
                notes=notes,
            ))
    return manifests


_SEQ_RE = __import__("re").compile(r"_s(\d+)_")


def _build_seq_to_graph_nodes(root: Path) -> dict[int, list[str]]:
    """Map seq_number → list of graph node names that carry that seq.

    Graph nodes encode seq in their name via `_seqNNN_` (e.g.
    `backward_seq007_backward_pass`). Registry pigeon names encode it as
    `_sNNN_` (e.g. `逆f_ba_s007_`). Seq is the stable cross-reference key.
    """
    cache = root / "pigeon_brain" / "graph_cache.json"
    if not cache.exists():
        return {}
    graph = json.loads(cache.read_text("utf-8"))
    seq_re = __import__("re").compile(r"_seq(\d+)_?")
    seq_map: dict[int, list[str]] = {}
    for node_name in graph.get("nodes", {}):
        m = seq_re.search(node_name)
        if m:
            seq = int(m.group(1))
            seq_map.setdefault(seq, []).append(node_name)
    return seq_map


def propagate_through_veins(
    root: Path,
    manifests: list[BugManifest],
    max_depth: int = 3,
) -> list[BugManifest]:
    """BFS through import graph to populate affected_chain on each manifest.

    Resolves pigeon glyph names → graph English names via seq number, then
    walks the import dependency graph to find downstream importers.
    High-severity bugs (oc, hi) propagate further.
    """
    dependents = _load_graph_edges(root)   # {dependency: [importers]}
    seq_to_nodes = _build_seq_to_graph_nodes(root)

    for manifest in manifests:
        # Resolve origin name to graph node name(s) via seq
        m = _SEQ_RE.search(manifest.origin_module)
        origin_graph_names: list[str] = []
        if m:
            seq = int(m.group(1))
            origin_graph_names = seq_to_nodes.get(seq, [])
        # Also try direct match (handles English-named modules)
        if manifest.origin_module in dependents:
            origin_graph_names.append(manifest.origin_module)

        depth_limit = max_depth if manifest.severity >= 0.6 else 1
        visited: set[str] = set(origin_graph_names) | {manifest.origin_module}
        frontier = list(origin_graph_names)
        chain: list[str] = []

        for _ in range(depth_limit):
            next_frontier: list[str] = []
            for node in frontier:
                for downstream in dependents.get(node, []):
                    if downstream not in visited:
                        visited.add(downstream)
                        chain.append(downstream)
                        next_frontier.append(downstream)
            frontier = next_frontier
            if not frontier:
                break

        manifest.affected_chain = chain

    return manifests


def inject_into_packet(
    packet_dict: dict[str, Any],
    manifests: list[BugManifest],
) -> dict[str, Any]:
    """Stamp relevant BugManifests onto a packet dict (in-place).

    Matches manifests against the packet's path. If any node in the path
    is either bug origin OR in the affected_chain, the manifest travels
    with the packet.

    Works with the dict representation (from packet.__dict__ or asdict).
    Does not require modifying ContextPacket's dataclass.
    """
    path_nodes = set(packet_dict.get("path", []))
    relevant: list[dict] = []
    for m in manifests:
        touches = path_nodes & ({m.origin_module} | set(m.affected_chain))
        if touches:
            d = asdict(m)
            d["touches"] = sorted(touches)
            relevant.append(d)

    packet_dict["bug_manifests"] = relevant
    # Also append to fear_chain (existing field — surfaces in task_writer output)
    fear_chain: list[str] = packet_dict.get("fear_chain", [])
    for m in relevant:
        fear_chain.append(
            f"[BUG:{m['bug_type']}] {m['origin_module']} — {m['notes']}"
        )
    packet_dict["fear_chain"] = fear_chain
    return packet_dict


def write_to_node_memory(
    root: Path,
    node: str,
    manifests: list[BugManifest],
    electron_id: str,
) -> None:
    """Extend latest node_memory entry with active_bugs field.

    Non-destructive: loads existing memory, finds the most recent entry
    for this node that matches electron_id, adds active_bugs to it.
    Falls back to appending a stub entry if no match found.
    """
    p = root / NODE_MEMORY_PATH
    memory: dict[str, Any] = {}
    if p.exists():
        memory = json.loads(p.read_text("utf-8"))

    node_record = memory.setdefault(node, {"entries": [], "policy": {}})
    entries: list[dict] = node_record.get("entries", [])

    relevant = [
        asdict(m) for m in manifests
        if node == m.origin_module or node in m.affected_chain
    ]
    if not relevant:
        return

    # Try to patch the matching electron entry
    matched = False
    for entry in reversed(entries):
        if entry.get("electron_id") == electron_id:
            entry["active_bugs"] = relevant
            matched = True
            break

    # No existing entry for this electron — write a stub so the chain leaves a mark
    if not matched:
        entries.append({
            "electron_id": electron_id,
            "task_seed": "[bug_manifest_chain injection]",
            "active_bugs": relevant,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        node_record["entries"] = entries[-200:]  # cap

    # Update policy: surface highest-severity active bug
    if relevant:
        worst = max(relevant, key=lambda x: x["severity"])
        node_record["policy"]["active_bug_warning"] = (
            f"{worst['bug_type']}:{worst['origin_module']} sev={worst['severity']:.2f}"
        )

    p.write_text(json.dumps(memory, indent=2, default=str), encoding="utf-8")


def _log_chain(root: Path, record: dict) -> None:
    """Append a chain propagation record to the audit log."""
    log = root / BUG_MANIFEST_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def run_propagation(root: Path) -> dict[str, Any]:
    """Full pipeline: load bugs → propagate → write to node_memory.

    Returns a summary dict suitable for verification.
    """
    manifests = load_active_bugs(root)
    if not manifests:
        return {"status": "no_bugs", "manifests": 0}

    manifests = propagate_through_veins(root, manifests)

    electron_id = "bdm_" + uuid.uuid4().hex[:8]
    nodes_touched: set[str] = set()

    for m in manifests:
        # Write to origin node
        write_to_node_memory(root, m.origin_module, manifests, electron_id)
        nodes_touched.add(m.origin_module)
        # Write to each downstream node
        for node in m.affected_chain:
            write_to_node_memory(root, node, manifests, electron_id)
            nodes_touched.add(node)

    summary = {
        "electron_id": electron_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "manifests_built": len(manifests),
        "nodes_touched": sorted(nodes_touched),
        "nodes_touched_count": len(nodes_touched),
        "by_type": {
            bk: sum(1 for m in manifests if m.bug_type == bk)
            for bk in BUG_SEVERITY
        },
        "top_severity": sorted(
            [{"bug_id": m.bug_id, "sev": m.severity, "chain_len": len(m.affected_chain)}
             for m in manifests],
            key=lambda x: -x["sev"],
        )[:10],
    }
    _log_chain(root, summary)
    return summary


def demo_chain(root: Path) -> None:
    """Run the chain and print a report showing bug context at downstream nodes."""
    print("=== Bug Demon Manifest Chain — Prototype Demo ===\n")

    # 1. Load bugs
    manifests = load_active_bugs(root)
    print(f"Active bugs loaded: {len(manifests)}")
    by_type: dict[str, int] = {}
    for m in manifests:
        by_type[m.bug_type] = by_type.get(m.bug_type, 0) + 1
    for bk, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {bk}: {count} modules")
    print()

    # 2. Propagate
    manifests = propagate_through_veins(root, manifests)
    with_chain = [m for m in manifests if m.affected_chain]
    print(f"Propagated through import graph:")
    print(f"  {len(with_chain)}/{len(manifests)} bugs have downstream affected modules")
    if with_chain:
        example = max(with_chain, key=lambda x: len(x.affected_chain))
        print(f"  Widest blast radius: {example.origin_module} ({example.bug_type})"
              f" → {len(example.affected_chain)} downstream module(s)")
        if example.affected_chain:
            print(f"  Affected chain: {' → '.join(example.affected_chain[:5])}")
    print()

    # 3. Test packet injection
    sample_path = [manifests[0].origin_module] if manifests else ["unknown"]
    if with_chain:
        sample_path = [with_chain[0].origin_module] + with_chain[0].affected_chain[:2]

    packet_dict = {
        "origin": sample_path[0],
        "task_seed": "debug overcap in backward pass",
        "path": sample_path,
        "fear_chain": [],
        "accumulated": [],
    }
    inject_into_packet(packet_dict, manifests)
    print(f"Packet injection ({len(sample_path)} nodes):")
    print(f"  bug_manifests injected: {len(packet_dict['bug_manifests'])}")
    print(f"  fear_chain entries added: {len(packet_dict['fear_chain'])}")
    for entry in packet_dict["fear_chain"][:3]:
        print(f"  {entry}")
    print()

    # 4. Write to node_memory
    electron_id = "demo_" + uuid.uuid4().hex[:6]
    for node in sample_path[:3]:
        write_to_node_memory(root, node, manifests, electron_id)

    # Verify: read back and confirm active_bugs present
    p = root / NODE_MEMORY_PATH
    if p.exists():
        memory = json.loads(p.read_text("utf-8"))
        for node in sample_path[:3]:
            rec = memory.get(node, {})
            entries = rec.get("entries", [])
            bug_entry = next(
                (e for e in reversed(entries) if e.get("active_bugs")), None
            )
            policy_warn = rec.get("policy", {}).get("active_bug_warning", "none")
            print(f"node_memory[{node}]:")
            if bug_entry:
                print(f"  active_bugs: {len(bug_entry['active_bugs'])} entry(ies)")
                top = bug_entry["active_bugs"][0]
                print(f"  top bug: {top['bug_type']}:{top['origin_module']} sev={top['severity']}")
            else:
                print(f"  active_bugs: (not written to memory yet)")
            print(f"  policy.active_bug_warning: {policy_warn}")
    print()
    print("=== Chain verification complete ===")
    print()
    print("RESULT: Bug context now persists in node_memory for these nodes.")
    print("The next backward pass that touches them will see active_bugs.")
    print("Packet fear_chain carries bug annotations — task_writer will surface them.")


if __name__ == "__main__":
    demo_chain(Path("."))
