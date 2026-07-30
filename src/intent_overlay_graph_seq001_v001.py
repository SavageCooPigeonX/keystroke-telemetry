"""Build a provenance-aware overlay graph for intent resurfacing.

The prompt extractor stays stateless. This bridge decides whether a repeated
intent is just context recall or rework after an attempted outcome cycle.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.intent_overlay_sources_seq001_v001 import (
    append_jsonl,
    collect_overlay_events,
    infer_intent_key_from_edit,
    now_iso,
    write_json,
)

SCHEMA = "intent_overlay_graph/v1"
OUT_JSON = "logs/intent_overlay_graph.json"
OUT_JSONL = "logs/intent_overlay_events.jsonl"


def _new_node(key: str) -> dict[str, Any]:
    return {
        "intent_key": key,
        "seen_count": 0,
        "attempt_count": 0,
        "rework_count": 0,
        "operator_rework_count": 0,
        "agent_rework_count": 0,
        "files": [],
        "status": "new",
    }


def _classify_event(event: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    prior_attempts = int(node.get("attempt_count", 0))
    prior_status = str(node.get("status") or "new")
    source = str(event.get("source") or "")
    if event.get("status") in {"solved", "partial", "failed"}:
        return event
    if source == "operator_prompt":
        if prior_attempts and prior_status != "solved":
            event["status"] = "rework"
            event["rework_kind"] = "operator_intent_rework"
        elif node.get("seen_count"):
            event["status"] = "resurfaced"
        else:
            event["status"] = "new"
        return event
    if prior_attempts and prior_status != "solved":
        event["status"] = "rework"
        event["rework_kind"] = "agent_intent_rework"
    else:
        event["status"] = "attempted"
    return event


def _update_node(node: dict[str, Any], event: dict[str, Any]) -> None:
    status = event.get("status", node["status"])
    node["seen_count"] += 1
    node["last_seen_ts"] = event.get("ts")
    node["status"] = status
    files = [item for item in event.get("files", []) if item]
    node["files"] = sorted(set([*node.get("files", []), *files]))
    if status in {"attempted", "partial", "failed", "solved", "rework"}:
        if event.get("source") != "operator_prompt":
            node["attempt_count"] += 1
    if status == "rework":
        node["rework_count"] += 1
        if event.get("rework_kind") == "operator_intent_rework":
            node["operator_rework_count"] += 1
        if event.get("rework_kind") == "agent_intent_rework":
            node["agent_rework_count"] += 1


def classify_overlay_events(events: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    classified: list[dict[str, Any]] = []
    for event in events:
        key = str(event["intent_key"])
        node = nodes.setdefault(key, _new_node(key))
        event = _classify_event(dict(event), node)
        _update_node(node, event)
        classified.append(event)
    return nodes, classified


def build_intent_overlay(root: Path, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    nodes, events = classify_overlay_events(collect_overlay_events(root))
    graph = {
        "schema": SCHEMA,
        "updated_at": now_iso(),
        "node_count": len(nodes),
        "event_count": len(events),
        "rework_count": sum(n["rework_count"] for n in nodes.values()),
        "nodes": sorted(nodes.values(), key=lambda row: (-row["rework_count"], row["intent_key"])),
        "recent_events": events[-50:],
    }
    if write:
        write_json(root / OUT_JSON, graph)
        append_jsonl(root / OUT_JSONL, events[-100:])
    return graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bridge intent logs into an overlay graph.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    graph = build_intent_overlay(Path(args.root), write=not args.no_write)
    print(json.dumps({
        "schema": graph["schema"],
        "nodes": graph["node_count"],
        "rework": graph["rework_count"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
