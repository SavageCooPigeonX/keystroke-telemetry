"""Build a provenance-aware overlay graph for intent resurfacing.

The prompt extractor can stay stateless. This bridge reads the durable logs and
decides whether a repeated intent is just context recall or rework after an
attempted outcome cycle.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "intent_overlay_graph/v1"
EVENT_SCHEMA = "intent_overlay_event/v1"
OUT_JSON = "logs/intent_overlay_graph.json"
OUT_JSONL = "logs/intent_overlay_events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _load_jsonl(path: Path, limit: int = 2000) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows[-limit:]


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def canonical_intent_key(intent_key: str) -> str:
    """Normalize generated keys while keeping their scope:verb:target:scale shape."""
    parts = [re.sub(r"[^a-z0-9_./-]+", "_", p.lower()).strip("_") for p in str(intent_key or "").split(":")]
    parts = [p for p in parts if p]
    return ":".join(parts[:4]) if parts else ""


def _tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-zA-Z0-9_]+", str(text or "").lower()) if len(tok) > 2]


def _verb(text: str) -> str:
    tokens = set(_tokens(text))
    if tokens & {"fix", "repair", "bug", "broken", "failed", "failing"}:
        return "repair"
    if tokens & {"test", "verify", "audit", "check"}:
        return "test"
    if tokens & {"refactor", "split", "rename", "rewrite"}:
        return "refactor"
    if tokens & {"delete", "remove", "prune"}:
        return "delete"
    if tokens & {"add", "build", "create", "implement", "wire"}:
        return "build"
    return "route"


def infer_intent_key_from_edit(row: dict[str, Any]) -> str:
    """Best-effort realized-intent key for edit-only Cursor/Codex events."""
    for key in ("intent_key", "agent_intent_key", "realized_intent_key", "codex_intent_key"):
        value = str(row.get(key) or "")
        if ":" in value:
            return value
    loop = row.get("intent_loop_binding") if isinstance(row.get("intent_loop_binding"), dict) else {}
    value = str(loop.get("intent_key") or row.get("prompt_intent") or "")
    if ":" in value:
        return value
    file_path = str(row.get("file") or row.get("path") or "unknown").replace("\\", "/")
    scope = str(Path(file_path).parent).replace("\\", "/") if "/" in file_path else "root"
    if scope in {"", "."}:
        scope = "root"
    target = Path(file_path).stem or "unknown"
    why = " ".join(str(row.get(k) or "") for k in ("edit_why", "prompt_msg", "reason"))
    scale = "patch" if int(row.get("added") or 0) or int(row.get("removed") or 0) else "minor"
    return f"{scope}:{_verb(why)}:{target}:{scale}"


def _operator_events(root: Path) -> list[dict[str, Any]]:
    events = []
    for row in _load_jsonl(root / "logs" / "intent_keys.jsonl"):
        intent_key = canonical_intent_key(str(row.get("intent_key") or ""))
        if not intent_key:
            continue
        events.append({
            "schema": EVENT_SCHEMA,
            "ts": row.get("ts") or _now(),
            "intent_key": intent_key,
            "source": "operator_prompt",
            "pass": "forward",
            "prompt": row.get("prompt", ""),
            "files": [row.get("manifest_path")] if row.get("manifest_path") else [],
            "evidence": [{"type": "intent_key_row", "confidence": row.get("confidence", 0)}],
        })
    return events


def _edit_events(root: Path) -> list[dict[str, Any]]:
    events = []
    for row in _load_jsonl(root / "logs" / "edit_pairs.jsonl"):
        intent_key = canonical_intent_key(infer_intent_key_from_edit(row))
        if not intent_key:
            continue
        source = str(row.get("source") or row.get("edit_author") or "agent_edit")
        events.append({
            "schema": EVENT_SCHEMA,
            "ts": row.get("edit_ts") or row.get("ts") or _now(),
            "intent_key": intent_key,
            "source": "agent_edit" if source in {"codex", "copilot", "cursor", "unknown"} else source,
            "pass": "backward",
            "prompt": row.get("prompt_msg", ""),
            "files": [row.get("file")] if row.get("file") else [],
            "attempt_id": row.get("edit_hash") or row.get("response_id") or "",
            "evidence": [{"type": "edit_pair", "match_score": row.get("match_score", 0)}],
        })
    return events


def _outcome_events(root: Path) -> list[dict[str, Any]]:
    events = []
    for row in _load_jsonl(root / "logs" / "file_solution_outcomes.jsonl"):
        intent_key = canonical_intent_key(infer_intent_key_from_edit(row))
        if not intent_key:
            continue
        score = row.get("outcome_score") if isinstance(row.get("outcome_score"), dict) else {}
        verdict = str(score.get("verdict") or "keep_watch")
        status = {"strengthen_path": "solved", "keep_watch": "partial", "weaken_path": "failed"}.get(verdict, "partial")
        events.append({
            "schema": EVENT_SCHEMA,
            "ts": row.get("ts") or _now(),
            "intent_key": intent_key,
            "source": "outcome_score",
            "pass": "backward",
            "status": status,
            "files": [row.get("file")] if row.get("file") else [],
            "attempt_id": row.get("commit") or "",
            "outcome_score": score,
            "evidence": [{"type": "solution_outcome", "verdict": verdict}],
        })
    return events


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


def build_intent_overlay(root: Path, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    events = [*_operator_events(root), *_edit_events(root), *_outcome_events(root)]
    events.sort(key=lambda row: str(row.get("ts") or ""))
    nodes: dict[str, dict[str, Any]] = {}
    classified: list[dict[str, Any]] = []
    for event in events:
        key = str(event["intent_key"])
        node = nodes.setdefault(key, {
            "intent_key": key, "seen_count": 0, "attempt_count": 0, "rework_count": 0,
            "operator_rework_count": 0, "agent_rework_count": 0, "files": [], "status": "new",
        })
        event = _classify_event(event, node)
        node["seen_count"] += 1
        node["last_seen_ts"] = event.get("ts")
        node["status"] = event.get("status", node["status"])
        node["files"] = sorted(set([*node.get("files", []), *[f for f in event.get("files", []) if f]]))
        if event["status"] in {"attempted", "partial", "failed", "solved", "rework"}:
            node["attempt_count"] += 1 if event.get("source") != "operator_prompt" else 0
        if event["status"] == "rework":
            node["rework_count"] += 1
            if event.get("rework_kind") == "operator_intent_rework":
                node["operator_rework_count"] += 1
            if event.get("rework_kind") == "agent_intent_rework":
                node["agent_rework_count"] += 1
        classified.append(event)
    graph = {
        "schema": SCHEMA,
        "updated_at": _now(),
        "node_count": len(nodes),
        "event_count": len(classified),
        "rework_count": sum(n["rework_count"] for n in nodes.values()),
        "nodes": sorted(nodes.values(), key=lambda row: (-row["rework_count"], row["intent_key"])),
        "recent_events": classified[-50:],
    }
    if write:
        _write_json(root / OUT_JSON, graph)
        _append_jsonl(root / OUT_JSONL, classified[-100:])
    return graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bridge intent logs into an overlay graph.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    graph = build_intent_overlay(Path(args.root), write=not args.no_write)
    print(json.dumps({"schema": graph["schema"], "nodes": graph["node_count"], "rework": graph["rework_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
