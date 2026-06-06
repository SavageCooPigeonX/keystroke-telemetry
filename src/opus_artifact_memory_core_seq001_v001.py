"""Core writer for Opus artifact memory."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.opus_artifact_memory_signals_seq001_v001 import (
    compiler_probe,
    file_death_areas,
    file_dialogue,
    focus_files,
    git_touch_counts,
    high_touch_files,
    memory_directive,
    telemetry_read,
)

SCHEMA = "opus_artifact_memory/v1"
LATEST = "logs/opus_artifact_memory_latest.json"
HISTORY = "logs/opus_artifact_memory.jsonl"
MARKDOWN = "logs/opus_artifact_memory.md"


def build_opus_artifact_memory(
    root: Path,
    prompt: str = "",
    *,
    write: bool = True,
    commit_limit: int = 160,
) -> dict[str, Any]:
    """Build the durable codebase memory Claude Opus can reference."""
    root = Path(root)
    telemetry = _json(root / "logs" / "prompt_telemetry_latest.json")
    graph = _json(root / "logs" / "file_intelligence_graph_latest.json")
    self_knowledge = _json(root / "logs" / "file_self_knowledge_latest.json")
    compression = _json(root / "build" / "compressed" / "STATS.json")
    training_pairs = _jsonl(root / "logs" / "training_pairs.jsonl")
    edit_pairs = _jsonl(root / "logs" / "edit_pairs.jsonl")
    git_touches, recent_touches = git_touch_counts(root, commit_limit)
    focus = focus_files(telemetry, graph, self_knowledge)
    high_touch = high_touch_files(git_touches, edit_pairs, focus)
    result = {
        "schema": SCHEMA,
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt or ((telemetry.get("latest_prompt") or {}).get("preview") or ""),
        "input_sources": {
            "prompt_telemetry": "logs/prompt_telemetry_latest.json",
            "file_graph": "logs/file_intelligence_graph_latest.json",
            "file_self_knowledge": "logs/file_self_knowledge_latest.json",
            "training_pairs": "logs/training_pairs.jsonl",
            "edit_pairs": "logs/edit_pairs.jsonl",
            "git_commits_sampled": commit_limit,
        },
        "telemetry_read": telemetry_read(telemetry, training_pairs, edit_pairs),
        "high_touch_files": high_touch[:12],
        "file_death_areas": file_death_areas(root, git_touches, recent_touches, edit_pairs, focus),
        "compiler_probe": compiler_probe(root, compression),
        "file_dialogue": file_dialogue(self_knowledge),
        "opus_memory_directive": memory_directive(high_touch, focus),
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_opus_artifact_memory(result), encoding="utf-8")
    return result


def render_opus_artifact_memory(memory: dict[str, Any]) -> str:
    lines = ["# Opus Artifact Memory", "", f"- prompt: {memory.get('prompt', '')}"]
    telemetry = memory.get("telemetry_read") or {}
    lines.append(f"- prompt telemetry age minutes: `{telemetry.get('prompt_age_min')}`")
    lines.append(f"- training pair status: `{telemetry.get('training_pair_status')}`")
    lines.extend(["", "## High Touch Files"])
    for row in memory.get("high_touch_files") or []:
        lines.append(f"- `{row['file']}` score={row['score']} git={row['git_touches']} edits={row['edit_pairs']}")
    lines.extend(["", "## File Death Areas"])
    for row in memory.get("file_death_areas") or []:
        lines.append(f"- `{row['file']}` {row['reason']} tests={row['nearby_tests']}")
    lines.extend(["", "## Compiler Probe"])
    probe = memory.get("compiler_probe") or {}
    lines.append(f"- status: `{probe.get('status')}`")
    for issue in probe.get("issues") or []:
        lines.append(f"- {issue}")
    lines.extend(["", "## File Dialogue"])
    for row in memory.get("file_dialogue") or []:
        lines.append(f"- `{row['file']}` {row['readiness']}: {row['quote']}")
    lines.extend(["", "## Opus Directive", memory.get("opus_memory_directive", "")])
    return "\n".join(lines) + "\n"


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")
