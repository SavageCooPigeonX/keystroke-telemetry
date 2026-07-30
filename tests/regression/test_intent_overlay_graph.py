import json
from pathlib import Path

from src.intent_overlay_graph_seq001_v001 import build_intent_overlay, infer_intent_key_from_edit


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def test_operator_intent_resurface_after_attempt_is_rework(tmp_path):
    logs = tmp_path / "logs"
    key = "cursor:adapt:intent_key_capture:patch"
    _append(logs / "intent_keys.jsonl", {
        "ts": "2026-06-01T20:00:00+00:00",
        "prompt": "capture cursor intent keys through edits",
        "intent_key": key,
        "confidence": 0.8,
        "manifest_path": "MANIFEST.md",
    })
    _append(logs / "edit_pairs.jsonl", {
        "ts": "2026-06-01T20:01:00+00:00",
        "edit_ts": "2026-06-01T20:01:00+00:00",
        "source": "cursor",
        "intent_key": key,
        "file": "src/cursor_bridge.py",
        "added": 12,
        "removed": 1,
    })
    _append(logs / "intent_keys.jsonl", {
        "ts": "2026-06-01T20:02:00+00:00",
        "prompt": "cursor intent key capture is still not resurfacing",
        "intent_key": key,
        "confidence": 0.82,
    })

    graph = build_intent_overlay(tmp_path)

    node = graph["nodes"][0]
    assert node["intent_key"] == key
    assert node["operator_rework_count"] == 1
    assert graph["rework_count"] == 1
    assert graph["recent_events"][-1]["status"] == "rework"
    assert graph["recent_events"][-1]["rework_kind"] == "operator_intent_rework"
    assert (logs / "intent_overlay_graph.json").exists()


def test_agent_intent_resurface_after_failed_outcome_is_rework(tmp_path):
    logs = tmp_path / "logs"
    key = "codex:repair:overlay_bridge:patch"
    _append(logs / "edit_pairs.jsonl", {
        "edit_ts": "2026-06-01T20:03:00+00:00",
        "source": "codex_runtime",
        "intent_key": key,
        "file": "src/intent_overlay_graph_seq001_v001.py",
        "added": 20,
        "removed": 0,
    })
    _append(logs / "file_solution_outcomes.jsonl", {
        "ts": "2026-06-01T20:04:00+00:00",
        "intent_key": key,
        "file": "src/intent_overlay_graph_seq001_v001.py",
        "outcome_score": {"verdict": "weaken_path"},
    })
    _append(logs / "edit_pairs.jsonl", {
        "edit_ts": "2026-06-01T20:05:00+00:00",
        "source": "codex_runtime",
        "intent_key": key,
        "file": "src/intent_overlay_graph_seq001_v001.py",
        "added": 3,
        "removed": 3,
    })

    graph = build_intent_overlay(tmp_path)

    node = graph["nodes"][0]
    assert node["status"] == "rework"
    assert node["agent_rework_count"] == 1
    assert graph["recent_events"][-1]["rework_kind"] == "agent_intent_rework"


def test_edit_only_cursor_event_gets_realized_intent_key():
    row = {
        "file": "client/cursor_bridge.py",
        "edit_why": "fix cursor hooks for intent overlay",
        "added": 5,
        "removed": 0,
    }

    assert infer_intent_key_from_edit(row) == "client:repair:cursor_bridge:patch"
