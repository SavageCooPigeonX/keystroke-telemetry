"""Durable intent nodes grown from self-clearing intent graphs.

Intent nodes are the memory layer between raw prompt matching and file sims:
when a prompt's forward pass selects/deranks files, the surviving cluster is
folded into a node. Future prompts can wake that node before picking files.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "intent_nodes/v1"


def accumulate_intent_nodes(root: Path, graph: dict[str, Any], write: bool = True) -> dict[str, Any]:
    root = Path(root)
    state = _load_state(root)
    selected = (graph.get("context_clearing_pass") or {}).get("selected_files") or []
    deranked = (graph.get("context_clearing_pass") or {}).get("deranked_files") or []
    selected_by_intent = _files_by_intent(selected)
    deranked_by_intent = _files_by_intent(deranked)
    touched = []
    for intent in graph.get("intents") or []:
        key = _node_key(intent)
        node = state["nodes"].setdefault(key, _new_node(key, intent))
        intent_key = str(intent.get("intent_key") or "")
        files = selected_by_intent.get(intent_key) or [
            item for item in selected
            if str(item.get("file") or "") in set(intent.get("files") or [])
        ]
        if not files:
            files = [
                {"file": rel, "final_score": 0.25, "reasons": ["intent listed file before clearing"]}
                for rel in (intent.get("files") or [])[:4]
                if (root / rel).exists()
            ]
        _update_node(node, graph, intent, files, deranked_by_intent.get(intent_key, []))
        touched.append(_node_summary(node))
    state["updated_at"] = _now()
    summary = {
        "schema": "intent_node_update/v1",
        "ts": state["updated_at"],
        "graph_id": graph.get("graph_id", ""),
        "nodes_touched": touched,
        "node_count": len(state["nodes"]),
        "paths": {
            "latest": "logs/intent_nodes_latest.json",
            "state": "logs/intent_nodes.json",
            "history": "logs/intent_nodes_history.jsonl",
            "markdown": "logs/intent_nodes.md",
        },
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "intent_nodes.json", state)
        _write_json(logs / "intent_nodes_latest.json", summary)
        _append_jsonl(logs / "intent_nodes_history.jsonl", summary)
        (logs / "intent_nodes.md").write_text(render_intent_nodes(state), encoding="utf-8")
    return summary


def match_intent_nodes(root: Path, text: str, limit: int = 5) -> list[dict[str, Any]]:
    state = _load_state(Path(root))
    prompt_tokens = set(_tokens(text))
    matches = []
    for node in (state.get("nodes") or {}).values():
        node_tokens = set(node.get("tokens") or [])
        overlap = prompt_tokens & node_tokens
        if not overlap:
            continue
        score = len(overlap) * 0.8 + min(float(node.get("prompt_count") or 0), 12) * 0.08
        score += min(len(node.get("dominant_files") or []), 5) * 0.05
        matches.append({
            "node_id": node.get("node_id"),
            "node_key": node.get("node_key"),
            "score": round(score, 4),
            "overlap": sorted(overlap)[:8],
            "dominant_files": node.get("dominant_files", [])[:8],
            "prompt_count": node.get("prompt_count", 0),
            "last_prompt": node.get("last_prompt", ""),
        })
    matches.sort(key=lambda item: (item["score"], item["prompt_count"]), reverse=True)
    return matches[: max(1, int(limit or 5))]


def render_intent_nodes(state: dict[str, Any]) -> str:
    nodes = sorted(
        (state.get("nodes") or {}).values(),
        key=lambda item: (int(item.get("prompt_count") or 0), item.get("updated_at", "")),
        reverse=True,
    )
    lines = [
        "# Intent Nodes",
        "",
        "Durable clusters grown from self-clearing file sims.",
        "",
        f"- nodes: `{len(nodes)}`",
        f"- updated_at: `{state.get('updated_at', '')}`",
        "",
    ]
    for node in nodes[:40]:
        lines.extend([
            f"## {node.get('node_key')}",
            "",
            f"- prompts: `{node.get('prompt_count', 0)}`",
            f"- confidence_avg: `{node.get('confidence_avg', 0)}`",
            f"- dominant_files: `{', '.join(node.get('dominant_files', [])[:8]) or 'none'}`",
            f"- deranked_recent: `{', '.join(node.get('deranked_recent', [])[:6]) or 'none'}`",
            f"- last_prompt: {node.get('last_prompt', '')[:240]}",
            "",
        ])
    return "\n".join(lines)


def _load_state(root: Path) -> dict[str, Any]:
    path = root / "logs" / "intent_nodes.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(data, dict) and data.get("schema") == SCHEMA:
                data.setdefault("nodes", {})
                return data
        except Exception:
            pass
    return {"schema": SCHEMA, "created_at": _now(), "updated_at": _now(), "nodes": {}}


def _new_node(key: str, intent: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": "inode-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16],
        "node_key": key,
        "scope": intent.get("scope", ""),
        "verb_counts": {},
        "target": intent.get("target", ""),
        "tokens": sorted(set(_tokens(" ".join([key, intent.get("segment", ""), intent.get("intent_key", "")])))),
        "prompt_count": 0,
        "file_scores": {},
        "dominant_files": [],
        "deranked_recent": [],
        "examples": [],
        "confidence_sum": 0.0,
        "confidence_avg": 0.0,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _update_node(
    node: dict[str, Any],
    graph: dict[str, Any],
    intent: dict[str, Any],
    selected_files: list[dict[str, Any]],
    deranked_files: list[dict[str, Any]],
) -> None:
    node["prompt_count"] = int(node.get("prompt_count") or 0) + 1
    verb = str(intent.get("verb") or "route")
    verbs = node.setdefault("verb_counts", {})
    verbs[verb] = int(verbs.get(verb) or 0) + 1
    node["confidence_sum"] = round(float(node.get("confidence_sum") or 0.0) + float(intent.get("confidence") or 0), 4)
    node["confidence_avg"] = round(float(node["confidence_sum"]) / max(1, int(node["prompt_count"])), 4)
    node["last_prompt"] = str(graph.get("prompt") or "")[:500]
    node["updated_at"] = _now()
    node["tokens"] = sorted(set([*node.get("tokens", []), *_tokens(intent.get("segment", ""))]))
    scores = node.setdefault("file_scores", {})
    for item in selected_files:
        rel = str(item.get("file") or "").replace("\\", "/")
        if not rel:
            continue
        current = scores.setdefault(rel, {"score": 0.0, "selected_count": 0, "last_reasons": []})
        current["score"] = round(float(current.get("score") or 0.0) + max(float(item.get("final_score") or 0.1), 0.1), 4)
        current["selected_count"] = int(current.get("selected_count") or 0) + 1
        current["last_reasons"] = list(item.get("reasons") or [])[:4]
    for item in deranked_files:
        rel = str(item.get("file") or "").replace("\\", "/")
        if not rel:
            continue
        current = scores.setdefault(rel, {"score": 0.0, "selected_count": 0, "last_reasons": []})
        current["score"] = round(float(current.get("score") or 0.0) - 0.35, 4)
        current["last_derank_reasons"] = list(item.get("derank_reasons") or [])[:4]
    ranked = sorted(scores.items(), key=lambda pair: (float(pair[1].get("score") or 0.0), int(pair[1].get("selected_count") or 0)), reverse=True)
    node["dominant_files"] = [rel for rel, data in ranked if float(data.get("score") or 0.0) > 0][:10]
    node["deranked_recent"] = [str(item.get("file") or "") for item in deranked_files[:8]]
    examples = list(node.get("examples") or [])
    examples.append({
        "ts": graph.get("ts"),
        "graph_id": graph.get("graph_id"),
        "segment": intent.get("segment"),
        "prompt": str(graph.get("prompt") or "")[:240],
    })
    node["examples"] = examples[-8:]


def _files_by_intent(files: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for item in files:
        for intent_key in item.get("supporting_intents") or []:
            out.setdefault(str(intent_key), []).append(item)
    return out


def _node_key(intent: dict[str, Any]) -> str:
    scope = str(intent.get("scope") or "root")
    verb = str(intent.get("verb") or "route")
    target = str(intent.get("target") or "work")
    return f"{scope}:{verb}:{target}"


def _node_summary(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": node.get("node_id"),
        "node_key": node.get("node_key"),
        "prompt_count": node.get("prompt_count"),
        "dominant_files": node.get("dominant_files", [])[:6],
        "confidence_avg": node.get("confidence_avg", 0),
    }


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower())
        if len(token) >= 3 and token not in {"the", "and", "for", "with", "that", "this", "from"}
    ]


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["accumulate_intent_nodes", "match_intent_nodes", "render_intent_nodes"]
