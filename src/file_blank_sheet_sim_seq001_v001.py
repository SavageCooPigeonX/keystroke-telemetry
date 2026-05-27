"""Let files propose their own pressing state from recent repo memory."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LATEST = "logs/file_blank_sheet_sim_latest.json"
HISTORY = "logs/file_blank_sheet_sim.jsonl"
MARKDOWN = "logs/file_blank_sheet_sim.md"


def build_file_blank_sheet_sim(root: Path, *, write: bool = True, limit: int = 15) -> dict[str, Any]:
    """Create file-authored pressure jobs without granting source writes."""
    root = Path(root)
    prompts = _jsonl(root / "logs" / "prompt_journal.jsonl", 12)
    edits = _jsonl(root / "logs" / "codex_edit_outcomes.jsonl", 30)
    sim = _json(root / "logs" / "file_self_sim_learning_latest.json")
    artifact = _json(root / "logs" / "opus_artifact_memory_latest.json")
    pressure = _pressure(root, prompts, edits, sim, artifact, limit)
    result = {
        "schema": "file_blank_sheet_sim/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": "files_choose_pressure_no_source_write",
        "source_memory": {
            "recent_prompts": len(prompts),
            "codex_outcomes": len(edits),
            "wake_files": len(sim.get("wake_order") or []),
            "artifact_hot_files": len(artifact.get("high_touch_files") or []),
        },
        "file_pressure_jobs": pressure,
        "approval_gate": {
            "file_sim": "files argue and approve local pressure",
            "opus": "turns pressure into job queue and grader criteria",
            "gemini": "selects context blocks per file",
            "deepseek": "writes only approved patch/test artifacts",
            "direct_source_write": False,
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_blank_sheet_sim(result), encoding="utf-8")
    return result


def render_blank_sheet_sim(sim: dict[str, Any]) -> str:
    lines = ["# File Blank Sheet Sim", "", f"- mode: `{sim.get('mode')}`", "", "## File Pressure Jobs"]
    for job in sim.get("file_pressure_jobs") or []:
        lines.append(f"- `{job['file']}` {job['pressing_state']}: {job['why']}")
    return "\n".join(lines) + "\n"


def _pressure(root: Path, prompts: list[dict[str, Any]], edits: list[dict[str, Any]], sim: dict[str, Any], artifact: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    reasons: dict[str, list[str]] = {}
    for row in edits:
        for file in row.get("files") or []:
            _add(counts, reasons, str(file), 5, "recent accepted Codex edit outcome")
    for row in sim.get("wake_order") or []:
        _add(counts, reasons, str(row.get("file")), 4, row.get("wake_reason") or "file sim woke me")
    for row in artifact.get("high_touch_files") or []:
        _add(counts, reasons, str(row.get("file")), 3, "high touch file")
    for row in artifact.get("file_death_areas") or []:
        _add(counts, reasons, str(row.get("file")), 4, row.get("reason") or "death area")
    prompt_text = " ".join(str(row.get("msg", "")) for row in prompts).lower()
    for path in root.glob("src/*.py"):
        stem = path.stem.lower()
        if any(token and token in prompt_text for token in stem.split("_")[:4]):
            _add(counts, reasons, path.as_posix(), 2, "recent prompt named my tokens")
    return [_job(file, score, reasons[file]) for file, score in counts.most_common(limit) if file and (root / file).exists()]


def _job(file: str, score: int, reasons: list[str]) -> dict[str, Any]:
    state = "write_test_first" if any("death" in r or "validation" in r for r in reasons) else "request_context_then_patch"
    return {
        "schema": "file_pressure_job/v1",
        "file": file,
        "pressure_score": score,
        "pressing_state": state,
        "why": "; ".join(dict.fromkeys(reasons))[:300],
        "file_text": f"I want a job because {', '.join(dict.fromkeys(reasons))[:220]}.",
        "allowed_next": ["context block", "test artifact", "patch artifact after approval"],
        "approval_required": ["file_sim", "opus_grader", "validation"],
    }


def _add(counts: Counter[str], reasons: dict[str, list[str]], file: str, score: int, reason: str) -> None:
    if not file:
        return
    counts[file] += score
    reasons.setdefault(file, []).append(str(reason))


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
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
