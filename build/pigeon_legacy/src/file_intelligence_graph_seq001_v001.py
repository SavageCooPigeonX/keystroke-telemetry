"""File intelligence graph for evidence-grounded file simulations.

This promotes file memory from loose notes into typed graph edges. The graph is
built from code structure plus telemetry traces, then rendered as compact
context for sims and intent routing.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

SCHEMA = "file_intelligence_graph/v1"

SOURCE_ROOTS = ("src", "pigeon_compiler", "pigeon_brain")
LOG_TAIL_LIMIT = 600
_NODE_CACHE: dict[str, tuple[float, dict[str, dict[str, Any]], dict[str, str]]] = {}

EDGE_WEIGHTS = {
    "imports": 0.9,
    "imported_by": 0.82,
    "dynamic_imports": 0.78,
    "tested_by": 0.76,
    "tests": 0.72,
    "co_touched_with": 0.68,
    "sim_requested": 0.66,
    "prompt_woke": 0.62,
    "edited_after_prompt": 0.58,
    "intent_key_matched": 0.54,
    "duplicate_identity": 0.52,
    "validated_with": 0.5,
}

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "about", "because",
    "file", "files", "test", "tests", "src", "logs", "root", "none", "true",
    "false", "patch", "build", "fix", "minor", "major", "read",
}


def build_file_intelligence_graph(
    root: Path,
    *,
    prompt: str = "",
    deleted_words: list[str] | None = None,
    focus_files: list[str] | None = None,
    write: bool = True,
    log_tail_limit: int = LOG_TAIL_LIMIT,
) -> dict[str, Any]:
    """Build a typed evidence graph from source structure and telemetry logs."""
    root = Path(root)
    deleted_words = deleted_words or []
    nodes, aliases = _discover_nodes(root)
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}

    def add_edge(src: str, dst: str, edge_type: str, weight: float | None = None, evidence: str = "") -> None:
        _add_edge(edges, src, dst, edge_type, weight, evidence)

    focus_ids = _focus_ids(focus_files or [], aliases, nodes)
    prompt_matches = _prompt_file_matches(prompt, nodes, limit=12)
    scan_ids = _dedupe([*focus_ids, *[row["id"] for row in prompt_matches[:10]]])
    _hydrate_nodes(root, nodes, scan_ids)
    _add_static_code_edges(root, nodes, aliases, add_edge, scan_ids=scan_ids)
    _add_test_edges(root, nodes, aliases, add_edge, scan_ids=scan_ids)
    _add_log_edges(root, nodes, aliases, add_edge, log_tail_limit=log_tail_limit)
    _add_prompt_edges(prompt, deleted_words, nodes, add_edge)
    _add_duplicate_edges(nodes, add_edge)

    edge_list = list(edges.values())
    _attach_degrees(nodes, edge_list)
    for row in prompt_matches:
        if row["id"] not in focus_ids:
            focus_ids.append(row["id"])
    packets = [_file_packet(file_id, nodes, edge_list) for file_id in focus_ids[:12]]
    graph_id = _graph_id(prompt, deleted_words, edge_list)
    now = _now()
    graph = {
        "schema": SCHEMA,
        "graph_id": graph_id,
        "ts": now,
        "prompt": prompt,
        "deleted_words": deleted_words,
        "node_count": len(nodes),
        "edge_count": len(edge_list),
        "focus_files": focus_ids,
        "prompt_matches": prompt_matches,
        "nodes": nodes,
        "edges": edge_list,
        "focus_packets": packets,
        "paths": {
            "state": "logs/file_intelligence_graph.json",
            "latest": "logs/file_intelligence_graph_latest.json",
            "history": "logs/file_intelligence_graph_history.jsonl",
            "markdown": "logs/file_intelligence_graph.md",
        },
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "file_intelligence_graph.json", _compact_graph(graph))
        _write_json(logs / "file_intelligence_graph_latest.json", _latest_graph(graph))
        _append_jsonl(logs / "file_intelligence_graph_history.jsonl", _latest_graph(graph))
        (logs / "file_intelligence_graph.md").write_text(render_file_intelligence_report(graph), encoding="utf-8")
    return graph


def expand_files_with_graph(
    root: Path,
    selected_files: list[dict[str, Any]],
    *,
    prompt: str = "",
    deleted_words: list[str] | None = None,
    limit: int = 6,
    write: bool = True,
) -> list[dict[str, Any]]:
    """Expand selected files with high-signal graph neighbors."""
    selected_files = list(selected_files or [])
    focus = [str(item.get("name") or item.get("file") or item.get("path") or "") for item in selected_files]
    graph = build_file_intelligence_graph(
        root,
        prompt=prompt,
        deleted_words=deleted_words or [],
        focus_files=focus,
        write=write,
    )
    nodes = graph.get("nodes") or {}
    edge_list = graph.get("edges") or []
    by_file: dict[str, dict[str, Any]] = {}

    def add_row(file_id: str, score: float, source: str, base: dict[str, Any] | None = None) -> None:
        if file_id not in nodes and not file_id.startswith("test_"):
            return
        row = by_file.setdefault(file_id, {
            "name": file_id,
            "score": 0.0,
            "sources": [],
        })
        row["score"] = round(max(float(row.get("score") or 0.0), score), 4)
        sources = list(row.get("sources") or [])
        if source not in sources:
            sources.append(source)
        row["sources"] = sources[:8]
        if base:
            for key in ("snippet", "path", "file"):
                if base.get(key) and not row.get(key):
                    row[key] = base[key]

    selected_ids: list[str] = []
    aliases = _aliases_from_nodes(nodes)
    for item in selected_files:
        file_id = _resolve_alias(str(item.get("name") or item.get("file") or item.get("path") or ""), aliases, nodes)
        if not file_id:
            continue
        selected_ids.append(file_id)
        add_row(file_id, float(item.get("score") or item.get("final_score") or 0.45), "selected", item)

    prompt_scores = {row["id"]: float(row.get("score") or 0.0) for row in graph.get("prompt_matches") or []}
    for file_id, score in prompt_scores.items():
        add_row(file_id, 0.35 + score, "file_graph:prompt_match")

    selected_set = set(selected_ids)
    for edge in edge_list:
        src = str(edge.get("src") or "")
        dst = str(edge.get("dst") or "")
        edge_type = str(edge.get("type") or "")
        weight = float(edge.get("weight") or EDGE_WEIGHTS.get(edge_type, 0.4))
        if src in selected_set and dst in nodes:
            add_row(dst, 0.22 + weight * 0.58 + prompt_scores.get(dst, 0.0), f"file_graph:{edge_type}:{src}")
        if dst in selected_set and src in nodes:
            add_row(src, 0.18 + weight * 0.52 + prompt_scores.get(src, 0.0), f"file_graph:{edge_type}:{dst}")

    rows = list(by_file.values())
    rows.sort(key=lambda item: (float(item.get("score") or 0.0), len(item.get("sources") or [])), reverse=True)
    return rows[: max(1, int(limit or 6))]


def render_graph_context_for_files(
    root: Path,
    selected_files: list[dict[str, Any]],
    *,
    prompt: str = "",
    deleted_words: list[str] | None = None,
    max_packets: int = 6,
) -> str:
    """Render compact graph context for a model prompt."""
    focus = [str(item.get("name") or item.get("file") or item.get("path") or "") for item in selected_files]
    graph = build_file_intelligence_graph(
        root,
        prompt=prompt,
        deleted_words=deleted_words or [],
        focus_files=focus,
        write=True,
    )
    packets = graph.get("focus_packets") or []
    lines = [
        "FILE INTELLIGENCE GRAPH:",
        f"  graph_id={graph.get('graph_id')} nodes={graph.get('node_count')} edges={graph.get('edge_count')}",
    ]
    matches = graph.get("prompt_matches") or []
    if matches:
        lines.append("  prompt_woke:")
        for row in matches[:6]:
            lines.append(f"    {row['id']} score={row['score']:.3f} via {', '.join(row.get('tokens', [])[:5])}")
    for packet in packets[:max_packets]:
        lines.append(f"  FILE {packet.get('id')} path={packet.get('path', '')}")
        if packet.get("role_hint"):
            lines.append(f"    role={packet['role_hint'][:160]}")
        if packet.get("risks"):
            lines.append(f"    risks={'; '.join(packet['risks'][:3])}")
        for edge in packet.get("top_edges", [])[:6]:
            peer = edge["dst"] if edge.get("src") == packet.get("id") else edge.get("src")
            lines.append(
                f"    edge {edge.get('type')} {peer} w={float(edge.get('weight') or 0):.2f}: "
                f"{str(edge.get('evidence') or '')[:160]}"
            )
    return "\n".join(lines)


def render_file_intelligence_report(graph: dict[str, Any]) -> str:
    lines = [
        "# File Intelligence Graph",
        "",
        "Typed edge memory for source files, prompts, sims, edits, tests, and learned context.",
        "",
        f"- schema: `{graph.get('schema', SCHEMA)}`",
        f"- graph_id: `{graph.get('graph_id', '')}`",
        f"- nodes: `{graph.get('node_count', 0)}`",
        f"- edges: `{graph.get('edge_count', 0)}`",
        f"- focus_files: `{', '.join(graph.get('focus_files') or []) or 'none'}`",
        "",
    ]
    matches = graph.get("prompt_matches") or []
    if matches:
        lines.extend(["## Prompt Matches", ""])
        for row in matches[:12]:
            lines.append(f"- `{row['id']}` score `{row['score']:.3f}` via `{', '.join(row.get('tokens', [])[:6])}`")
        lines.append("")
    packets = graph.get("focus_packets") or []
    if packets:
        lines.extend(["## Focus Packets", ""])
        for packet in packets:
            lines.extend([
                f"### {packet.get('id')}",
                "",
                f"- path: `{packet.get('path', '')}`",
                f"- role: {packet.get('role_hint', '')[:240] or 'unknown'}",
                f"- degree: in `{packet.get('in_degree', 0)}` / out `{packet.get('out_degree', 0)}`",
            ])
            if packet.get("risks"):
                lines.append(f"- risks: `{'; '.join(packet.get('risks')[:5])}`")
            for edge in packet.get("top_edges", [])[:8]:
                peer = edge["dst"] if edge.get("src") == packet.get("id") else edge.get("src")
                lines.append(f"- `{edge.get('type')}` with `{peer}`: {str(edge.get('evidence') or '')[:220]}")
            lines.append("")
    return "\n".join(lines)


def _discover_nodes(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    cache_key = str(root.resolve())
    cached = _NODE_CACHE.get(cache_key)
    if cached and (_datetime_timestamp() - cached[0]) < 60:
        return {key: dict(value) for key, value in cached[1].items()}, dict(cached[2])

    nodes: dict[str, dict[str, Any]] = {}
    aliases: dict[str, str] = {}

    def add_node(path: Path, kind: str) -> None:
        try:
            rel = path.relative_to(root).as_posix()
        except Exception:
            rel = path.as_posix()
        node_id = _canonical_file_id(rel)
        try:
            stat = path.stat()
            size = stat.st_size
        except Exception:
            size = 0
        prefix = _read_prefix(path)
        node = nodes.setdefault(node_id, {
            "id": node_id,
            "path": rel,
            "kind": kind,
            "tokens": sorted(set(_tokens(f"{node_id} {rel} {prefix}"))),
            "line_count": prefix.count("\n"),
            "size": size,
            "duplicate_paths": [],
            "role_hint": _role_hint(prefix),
            "in_degree": 0,
            "out_degree": 0,
            "hydrated": False,
        })
        if node.get("path") != rel and rel not in node["duplicate_paths"]:
            node["duplicate_paths"].append(rel)
        for alias in _aliases_for_path(rel):
            aliases[alias] = node_id

    for src_root in SOURCE_ROOTS:
        folder = root / src_root
        if folder.exists():
            for path in folder.rglob("*.py"):
                if "__pycache__" not in path.parts:
                    add_node(path, "source")
    for path in root.glob("test_*.py"):
        add_node(path, "test")
    tests_dir = root / "tests"
    if tests_dir.exists():
        for path in tests_dir.rglob("test*.py"):
            add_node(path, "test")
    _NODE_CACHE[cache_key] = (_datetime_timestamp(), {key: dict(value) for key, value in nodes.items()}, dict(aliases))
    return nodes, aliases


def _hydrate_nodes(root: Path, nodes: dict[str, dict[str, Any]], ids: list[str]) -> None:
    for node_id in ids:
        node = nodes.get(node_id)
        if not node or node.get("hydrated"):
            continue
        path = root / str(node.get("path") or "")
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        node["tokens"] = sorted(set([*node.get("tokens", []), *_tokens(f"{node_id} {node.get('path')} {text[:5000]}")]))
        node["line_count"] = len(text.splitlines())
        node["size"] = len(text)
        node["role_hint"] = _role_hint(text)
        node["hydrated"] = True


def _add_static_code_edges(
    root: Path,
    nodes: dict[str, dict[str, Any]],
    aliases: dict[str, str],
    add_edge: Callable[[str, str, str, float | None, str], None],
    *,
    scan_ids: list[str],
) -> None:
    for node_id in scan_ids:
        node = nodes.get(node_id)
        if not node:
            continue
        if node.get("kind") != "source":
            continue
        path = root / str(node.get("path") or "")
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in _import_targets(text, aliases, nodes):
            if target == node_id:
                continue
            add_edge(node_id, target, "imports", None, f"{node_id} imports {target}")
            add_edge(target, node_id, "imported_by", None, f"{target} imported by {node_id}")
        for target in _dynamic_targets(text, aliases, nodes):
            if target == node_id:
                continue
            add_edge(node_id, target, "dynamic_imports", None, f"{node_id} resolves {target} dynamically")


def _add_test_edges(
    root: Path,
    nodes: dict[str, dict[str, Any]],
    aliases: dict[str, str],
    add_edge: Callable[[str, str, str, float | None, str], None],
    *,
    scan_ids: list[str],
) -> None:
    scan_set = set(scan_ids)
    for test_id, node in list(nodes.items()):
        if node.get("kind") != "test":
            continue
        path = root / str(node.get("path") or "")
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        targets = set(_import_targets(text, aliases, nodes))
        test_tokens = set(_tokens(test_id))
        for source_id, source_node in nodes.items():
            if source_node.get("kind") != "source":
                continue
            if source_id not in scan_set:
                continue
            if source_id in targets or len(test_tokens & set(_tokens(source_id))) >= 2:
                add_edge(source_id, test_id, "tested_by", None, f"{test_id} covers {source_id}")
                add_edge(test_id, source_id, "tests", None, f"{test_id} imports or names {source_id}")


def _add_log_edges(
    root: Path,
    nodes: dict[str, dict[str, Any]],
    aliases: dict[str, str],
    add_edge: Callable[[str, str, str, float | None, str], None],
    *,
    log_tail_limit: int,
) -> None:
    logs = root / "logs"
    for record in _jsonl_tail(logs / "intent_touches.jsonl", log_tail_limit):
        files = [_resolve_alias(str(item), aliases, nodes) for item in record.get("files") or []]
        files = [item for item in files if item]
        preview = str(record.get("prompt_preview") or record.get("prompt") or "")[:180]
        for file_id in files:
            add_edge("operator_prompt_history", file_id, "prompt_woke", None, preview)
        for a, b in combinations(sorted(set(files)), 2):
            add_edge(a, b, "co_touched_with", None, preview)
            add_edge(b, a, "co_touched_with", None, preview)

    for record in _jsonl_tail(logs / "edit_pairs.jsonl", log_tail_limit):
        file_id = _resolve_alias(str(record.get("file") or ""), aliases, nodes)
        if not file_id:
            continue
        why = str(record.get("edit_why") or record.get("prompt_msg") or "")[:220]
        add_edge("operator_prompt_history", file_id, "edited_after_prompt", None, why)
        prompt = str(record.get("prompt_msg") or "")
        for peer in _mentioned_files(prompt, nodes):
            if peer != file_id:
                add_edge(file_id, peer, "co_touched_with", 0.5, f"edit pair prompt also mentioned {peer}")

    for record in _jsonl_tail(logs / "sim_mailbox.jsonl", log_tail_limit):
        recipients = [_resolve_alias(str(record.get("to") or ""), aliases, nodes)]
        senders = [_resolve_alias(str(item), aliases, nodes) for item in record.get("from") or []]
        action = str(record.get("action_path") or record.get("intent") or "")[:220]
        for src in [item for item in senders if item]:
            for dst in [item for item in recipients if item]:
                if src != dst:
                    add_edge(src, dst, "sim_requested", None, action)

    for record in _jsonl_tail(logs / "intent_keys.jsonl", log_tail_limit):
        intent_key = str(record.get("intent_key") or "")
        prompt = str(record.get("prompt") or "")
        text = f"{intent_key} {prompt}"
        for file_id in _mentioned_files(text, nodes):
            add_edge("intent_key_history", file_id, "intent_key_matched", None, intent_key or prompt[:120])

    for record in _jsonl_tail(logs / "file_self_sim_learning_outcomes.jsonl", log_tail_limit):
        details = record.get("details") if isinstance(record.get("details"), dict) else {}
        file_id = _resolve_alias(str(record.get("file") or details.get("file") or ""), aliases, nodes)
        if not file_id:
            continue
        outcome = str(record.get("outcome") or "")
        reward = float(record.get("reward") or 0.0)
        add_edge("validation_gate", file_id, "validated_with", max(0.2, min(0.9, reward)), outcome[:180])


def _add_prompt_edges(
    prompt: str,
    deleted_words: list[str],
    nodes: dict[str, dict[str, Any]],
    add_edge: Callable[[str, str, str, float | None, str], None],
) -> None:
    text = " ".join([prompt or "", *(deleted_words or [])])
    for row in _prompt_file_matches(text, nodes, limit=12):
        add_edge("operator_prompt_current", row["id"], "prompt_woke", 0.45 + row["score"], f"matched {', '.join(row['tokens'][:6])}")


def _add_duplicate_edges(
    nodes: dict[str, dict[str, Any]],
    add_edge: Callable[[str, str, str, float | None, str], None],
) -> None:
    by_base: dict[str, list[str]] = defaultdict(list)
    for node_id in nodes:
        base = re.sub(r"^(test_)?", "", node_id)
        base = re.sub(r"(_v\d+|_seq\d+)$", "", base)
        by_base[base].append(node_id)
    for ids in by_base.values():
        if len(ids) < 2:
            continue
        for a, b in combinations(sorted(ids)[:6], 2):
            add_edge(a, b, "duplicate_identity", None, "similar canonical name")
            add_edge(b, a, "duplicate_identity", None, "similar canonical name")


def _import_targets(text: str, aliases: dict[str, str], nodes: dict[str, Any]) -> list[str]:
    targets: list[str] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        for item in ast.walk(tree):
            module = ""
            if isinstance(item, ast.ImportFrom):
                module = item.module or ""
                if item.level > 0 and module:
                    module = module.split(".", 1)[0]
                elif module.startswith("src."):
                    module = module.split(".", 1)[1].split(".", 1)[0]
                elif module.startswith(tuple(f"{root}." for root in SOURCE_ROOTS)):
                    module = module.split(".", 1)[1].split(".", 1)[0]
                else:
                    module = module.split(".", 1)[0]
                resolved = _resolve_alias(module, aliases, nodes)
                if resolved:
                    targets.append(resolved)
            elif isinstance(item, ast.Import):
                for alias in item.names:
                    name = alias.name
                    if name.startswith("src."):
                        name = name.split(".", 1)[1].split(".", 1)[0]
                    resolved = _resolve_alias(name, aliases, nodes)
                    if resolved:
                        targets.append(resolved)
    return _dedupe(targets)


def _dynamic_targets(text: str, aliases: dict[str, str], nodes: dict[str, Any]) -> list[str]:
    targets = []
    for match in re.findall(r"src_import\(\s*['\"]([^'\"]+)['\"]", text):
        resolved = _resolve_alias(match.split(".", 1)[0], aliases, nodes)
        if resolved:
            targets.append(resolved)
    return _dedupe(targets)


def _prompt_file_matches(prompt: str, nodes: dict[str, dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    prompt_tokens = set(_tokens(prompt))
    if not prompt_tokens:
        return []
    rows = []
    for node_id, node in nodes.items():
        node_tokens = set(node.get("tokens") or [])
        id_tokens = set(_tokens(node_id))
        overlap = prompt_tokens & (node_tokens | id_tokens)
        if not overlap:
            continue
        id_boost = 0.08 * len(prompt_tokens & id_tokens)
        score = round(min(1.0, len(overlap) / max(4, len(prompt_tokens)) + id_boost), 4)
        if score >= 0.08:
            rows.append({"id": node_id, "score": score, "tokens": sorted(overlap)})
    rows.sort(key=lambda item: (-item["score"], item["id"]))
    return rows[:limit]


def _file_packet(file_id: str, nodes: dict[str, dict[str, Any]], edge_list: list[dict[str, Any]]) -> dict[str, Any]:
    node = nodes.get(file_id, {"id": file_id, "path": "", "kind": "unknown"})
    connected = [edge for edge in edge_list if edge.get("src") == file_id or edge.get("dst") == file_id]
    connected.sort(key=lambda edge: float(edge.get("weight") or 0.0), reverse=True)
    risks = []
    if node.get("line_count", 0) > 220:
        risks.append(f"over_soft_cap:{node.get('line_count')}_lines")
    if node.get("duplicate_paths"):
        risks.append("duplicate_paths")
    if not connected:
        risks.append("orphan_no_edges")
    return {
        "id": file_id,
        "path": node.get("path", ""),
        "kind": node.get("kind", ""),
        "role_hint": node.get("role_hint", ""),
        "line_count": node.get("line_count", 0),
        "in_degree": node.get("in_degree", 0),
        "out_degree": node.get("out_degree", 0),
        "risks": risks,
        "top_edges": connected[:16],
    }


def _compact_graph(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes") or {}
    edges = graph.get("edges") or []
    return {
        "schema": graph.get("schema", SCHEMA),
        "graph_id": graph.get("graph_id"),
        "ts": graph.get("ts"),
        "node_count": graph.get("node_count"),
        "edge_count": graph.get("edge_count"),
        "focus_files": graph.get("focus_files"),
        "prompt_matches": graph.get("prompt_matches"),
        "nodes": nodes,
        "edges": edges,
    }


def _latest_graph(graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": f"{SCHEMA}_latest",
        "graph_id": graph.get("graph_id"),
        "ts": graph.get("ts"),
        "prompt": graph.get("prompt"),
        "deleted_words": graph.get("deleted_words"),
        "node_count": graph.get("node_count"),
        "edge_count": graph.get("edge_count"),
        "focus_files": graph.get("focus_files"),
        "prompt_matches": graph.get("prompt_matches"),
        "focus_packets": graph.get("focus_packets"),
    }


def _add_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    src: str,
    dst: str,
    edge_type: str,
    weight: float | None,
    evidence: str,
) -> None:
    src = str(src or "").strip()
    dst = str(dst or "").strip()
    if not src or not dst or src == dst:
        return
    key = (src, dst, edge_type)
    base = EDGE_WEIGHTS.get(edge_type, 0.42) if weight is None else float(weight)
    current = edges.get(key)
    if current is None:
        edges[key] = {
            "src": src,
            "dst": dst,
            "type": edge_type,
            "weight": round(base, 4),
            "count": 1,
            "evidence": str(evidence or "")[:260],
        }
    else:
        current["count"] = int(current.get("count") or 0) + 1
        current["weight"] = round(min(1.0, float(current.get("weight") or 0.0) + base * 0.08), 4)
        if evidence and evidence not in str(current.get("evidence") or ""):
            current["evidence"] = (str(current.get("evidence") or "") + " | " + str(evidence))[:260]


def _attach_degrees(nodes: dict[str, dict[str, Any]], edge_list: list[dict[str, Any]]) -> None:
    in_counts: dict[str, int] = defaultdict(int)
    out_counts: dict[str, int] = defaultdict(int)
    for edge in edge_list:
        out_counts[str(edge.get("src") or "")] += 1
        in_counts[str(edge.get("dst") or "")] += 1
    for node_id, node in nodes.items():
        node["in_degree"] = in_counts.get(node_id, 0)
        node["out_degree"] = out_counts.get(node_id, 0)


def _focus_ids(focus_files: list[str], aliases: dict[str, str], nodes: dict[str, Any]) -> list[str]:
    out = []
    for item in focus_files:
        resolved = _resolve_alias(str(item), aliases, nodes)
        if resolved and resolved not in out:
            out.append(resolved)
    return out


def _mentioned_files(text: str, nodes: dict[str, Any]) -> list[str]:
    lower = str(text or "").lower()
    out = []
    for node_id in nodes:
        if node_id in lower or node_id.replace("_", " ") in lower:
            out.append(node_id)
    return out[:10]


def _resolve_alias(value: str, aliases: dict[str, str], nodes: dict[str, Any]) -> str:
    if not value:
        return ""
    key = _canonical_file_id(value)
    if key in nodes:
        return key
    return aliases.get(key) or aliases.get(value.lower().replace("\\", "/")) or ""


def _aliases_from_nodes(nodes: dict[str, dict[str, Any]]) -> dict[str, str]:
    aliases = {}
    for node_id, node in nodes.items():
        for alias in _aliases_for_path(str(node.get("path") or node_id)):
            aliases[alias] = node_id
        aliases[node_id] = node_id
    return aliases


def _canonical_file_id(value: str) -> str:
    raw = str(value or "").replace("\\", "/").strip().strip("'\"")
    if not raw:
        return ""
    raw = raw.split("#", 1)[0]
    path = Path(raw)
    stem = path.stem if path.suffix else raw.rsplit("/", 1)[-1]
    stem = re.sub(r"_seq\d{3}.*$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"_s\d{3}.*$", "", stem, flags=re.IGNORECASE)
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")
    return stem


def _aliases_for_path(rel: str) -> set[str]:
    rel = rel.replace("\\", "/").lower()
    stem = Path(rel).stem
    canonical = _canonical_file_id(rel)
    aliases = {rel, stem, canonical, rel.removesuffix(".py")}
    if "/" in rel:
        aliases.add(rel.rsplit("/", 1)[-1].removesuffix(".py"))
    return {alias for alias in aliases if alias}


def _tokens(text: str) -> list[str]:
    return [
        item
        for item in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", str(text or "").lower().replace("-", "_"))
        if item not in STOP
    ]


def _role_hint(text: str) -> str:
    for line in str(text or "").splitlines()[:30]:
        clean = line.strip().strip('"').strip("'")
        if clean and not clean.startswith("#") and len(clean) > 20:
            return clean[:260]
    return ""


def _read_prefix(path: Path, limit: int = 4096) -> str:
    try:
        with path.open("rb") as handle:
            return handle.read(limit).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _jsonl_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    for line in lines[-max(1, int(limit or 1)):]:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _graph_id(prompt: str, deleted_words: list[str], edges: list[dict[str, Any]]) -> str:
    basis = "|".join([
        prompt[:400],
        " ".join(deleted_words[:20]),
        str(len(edges)),
        "".join(f"{e.get('src')}:{e.get('type')}:{e.get('dst')}" for e in edges[:100]),
    ])
    return "fig-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _datetime_timestamp() -> float:
    return datetime.now(timezone.utc).timestamp()
