"""Ambient codebase state for text-chain file mail."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_email_ambient_state(root: Path | None, record: dict[str, Any]) -> dict[str, Any]:
    """Read recent sim/runtime state so file mail can sound situated."""
    if root is None:
        return _fallback(record)
    root = Path(root)
    prompt = _latest_jsonl(root / "logs" / "prompt_journal.jsonl")
    sim = _json(root / "logs" / "file_self_sim_learning_latest.json")
    opus = _json(root / "logs" / "opus_orchestrator_runtime_latest.json")
    artifact = _json(root / "logs" / "opus_artifact_memory_latest.json")
    outcome = _json(root / "logs" / "codex_edit_outcome_latest.json")
    wake = sim.get("wake_order") if isinstance(sim.get("wake_order"), list) else []
    packets = sim.get("learning_packets") if isinstance(sim.get("learning_packets"), list) else []
    return {
        "operator": _snip(prompt.get("msg") or "", 360),
        "operator_state": prompt.get("cognitive_state", "unknown"),
        "recent_codex": _snip(outcome.get("reason") or "", 220),
        "hot_files": [row.get("file", "") for row in (artifact.get("high_touch_files") or [])[:5]],
        "wake_files": [row.get("file", "") for row in wake[:5]],
        "quotes": _quotes(packets, opus),
        "beefs": _beefs(record, wake, artifact),
        "job_count": ((opus.get("coding_area_memory") or {}).get("job_count")),
        "training": ((opus.get("artifact_memory") or {}).get("training_pair_status") or ""),
    }


def render_room_chat(record: dict[str, Any], ambient: dict[str, Any], sender: str, gate: dict[str, str]) -> list[str]:
    """Visible human layer: file-room group text."""
    beefs = ambient.get("beefs") or []
    quotes = ambient.get("quotes") or []
    hot = ambient.get("hot_files") or []
    wake = ambient.get("wake_files") or []
    lines = [
        "File room:",
        f"Nikita: {_snip(ambient.get('operator') or 'what changed?', 300)}",
        f"{sender}: I heard the complaint. The last version was a receipt. This one is the room talking.",
    ]
    if beefs:
        a, b, why = beefs[0]
        lines.append(f"{Path(a).name}: I have beef with `{b}` because {why}.")
    if len(beefs) > 1:
        a, b, why = beefs[1]
        lines.append(f"{Path(a).name}: Also `{b}` keeps showing up in my context window like unresolved weather: {why}.")
    lines.extend([
        f"Opus: Recent Codex move: {_snip(ambient.get('recent_codex') or 'no accepted edit outcome recorded yet', 220)}",
        f"Gemini/file reasoner: Hot files right now -> {', '.join(hot[:4]) or 'none'}",
        f"File sim: Woke files -> {', '.join(Path(x).name for x in wake[:4]) or sender}",
        f"Opus: Backward pass solution -> {gate['solution']}",
        f"{sender}: Approval -> {gate['approval']}",
        f"Grader: {gate['decision']}. DeepSeek only gets the job after file approval plus validation.",
    ])
    for quote in quotes[:3]:
        lines.append(f"{Path(quote[0]).name}: {quote[1]}")
    lines.extend([
        "Blank sheet:",
        f"{sender}: If you give files a blank page, they choose pressure from rename history, prompt heat, failed gates, and recent accepted Codex edits.",
        "Opus: I can orchestrate the sheet; I still do not write source. I write jobs, memory, and veto criteria.",
    ])
    return lines


def _beefs(record: dict[str, Any], wake: list[dict[str, Any]], artifact: dict[str, Any]) -> list[tuple[str, str, str]]:
    target = str(record.get("file") or "file")
    context = [str(x) for x in record.get("context_injection") or [] if x]
    out = []
    for ctx in context:
        if ctx != target:
            out.append((target, ctx, "it affects my validation path"))
    for row in (artifact.get("file_death_areas") or [])[:3]:
        file = row.get("file", "")
        if file and file != target:
            out.append((target, file, row.get("reason", "stale risk")))
    for row in wake[:3]:
        file = row.get("file", "")
        if file and file != target:
            out.append((file, target, row.get("wake_reason", "same sim room")))
    return out[:5]


def _quotes(packets: list[dict[str, Any]], opus: dict[str, Any]) -> list[tuple[str, str]]:
    rows = []
    for packet in packets:
        file = packet.get("file") or packet.get("target_file")
        quote = packet.get("file_quote") or packet.get("model_guide") or packet.get("status")
        if file and quote:
            rows.append((str(file), _snip(str(quote), 220)))
    for agent in opus.get("file_subagents") or []:
        if agent.get("file") and agent.get("quote"):
            rows.append((str(agent["file"]), _snip(str(agent["quote"]), 220)))
    return rows


def _fallback(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "operator": record.get("reason", ""),
        "operator_state": "unknown",
        "recent_codex": "",
        "hot_files": [],
        "wake_files": [record.get("file", "file")],
        "quotes": [],
        "beefs": [],
        "job_count": 0,
        "training": "",
    }


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _latest_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    for line in reversed(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            pass
    return {}


def _snip(text: str, limit: int) -> str:
    one = " ".join(str(text or "").split())
    return one if len(one) <= limit else one[: limit - 3].rstrip() + "..."
