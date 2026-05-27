"""Audit whether file sims are becoming useful collaborators."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.file_collaboration_comments_seq001_v001 import file_comments, manifest_state
from src.file_collaboration_metrics_seq001_v001 import (
    collaboration_metrics,
    collaboration_score,
    collaboration_verdict,
    missing_loops,
    operator_read,
    recommended_next_moves,
)
from src.file_collaboration_render_seq001_v001 import (
    render_file_collaboration_audit,
    render_manifest_collaboration_state,
)
from src.file_manifest_state_sync_seq001_v001 import sync_file_sim_manifest_state

SCHEMA = "file_collaboration_audit/v1"


def audit_file_collaboration(root: Path, intent: str = "", write: bool = True) -> dict[str, Any]:
    """Build a manifest-state collaboration readout from the latest file sim."""
    root = Path(root)
    logs = root / "logs"
    latest = _as_dict(_load_json(logs / "file_self_sim_learning_latest.json"))
    graph = latest.get("relationship_graph") or _as_dict(_load_json(logs / "file_relationship_graph.json"))
    history = _load_jsonl(logs / "file_self_sim_learning.jsonl", 40)
    outcomes = _load_jsonl(logs / "file_self_sim_learning_outcomes.jsonl", 240)
    registry = _as_dict(_load_json(logs / "file_identity_registry.json"))
    council = _as_dict(_load_json(logs / "file_job_council_latest.json"))
    packets = [item for item in latest.get("learning_packets", []) if isinstance(item, dict)]
    wake_order = [item for item in latest.get("wake_order", []) if isinstance(item, dict)]

    intent_model = latest.get("intent") if isinstance(latest.get("intent"), dict) else {}
    if intent:
        intent_model = {**intent_model, "raw": intent}

    metrics = collaboration_metrics(latest, graph, history, outcomes, council, logs)
    score = collaboration_score(metrics)
    verdict = collaboration_verdict(score, metrics)
    comments = file_comments(packets, graph, outcomes, registry)
    ts = _now()
    state = manifest_state(intent_model, metrics, verdict, comments, ts)
    result = {
        "schema": SCHEMA,
        "ts": ts,
        "root": str(root),
        "intent": intent_model,
        "verdict": verdict,
        "collaboration_score": score,
        "metrics": metrics,
        "operator_read": operator_read(verdict, metrics),
        "wake_files": [item.get("file", "") for item in wake_order[:12]],
        "manifest_state": state,
        "missing_loops": missing_loops(metrics),
        "recommended_next_moves": recommended_next_moves(metrics),
        "paths": {
            "latest": "logs/file_collaboration_audit_latest.json",
            "history": "logs/file_collaboration_audit.jsonl",
            "markdown": "logs/file_collaboration_audit.md",
            "manifest_state": "logs/file_manifest_collaboration_state.json",
            "manifest_state_markdown": "logs/file_manifest_collaboration_state.md",
            "comments": "logs/file_manifest_comments.jsonl",
        },
    }
    if write:
        _write_outputs(root, logs, result, state, comments)
    return result


def _write_outputs(
    root: Path,
    logs: Path,
    result: dict[str, Any],
    state: dict[str, Any],
    comments: list[dict[str, Any]],
) -> None:
    logs.mkdir(parents=True, exist_ok=True)
    _write_json(logs / "file_collaboration_audit_latest.json", result)
    _append_jsonl(logs / "file_collaboration_audit.jsonl", result)
    _write_json(logs / "file_manifest_collaboration_state.json", state)
    (logs / "file_collaboration_audit.md").write_text(render_file_collaboration_audit(result), encoding="utf-8")
    (logs / "file_manifest_collaboration_state.md").write_text(render_manifest_collaboration_state(state), encoding="utf-8")
    for comment in comments:
        _append_jsonl(logs / "file_manifest_comments.jsonl", comment)
    result["manifest_sync"] = sync_file_sim_manifest_state(root, result, write=True)
    _write_json(logs / "file_collaboration_audit_latest.json", result)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[-max(1, int(limit)):]:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
    except Exception:
        return rows
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")
