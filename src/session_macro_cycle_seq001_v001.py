"""Group recent agent prompts into macro verification cycles."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.session_macro_cycle_support_seq001_v001 import (
    append_jsonl,
    completion_evidence,
    deleted_words,
    group_cycles,
    jsonl,
    manifest_freshness,
    match_key,
    now,
    parse_ts,
    prompt_text,
    shatter_prompt,
    stable_id,
    unique,
    write_json,
)

SCHEMA = "session_macro_cycle/v1"
LATEST = "logs/session_macro_cycle_latest.json"
HISTORY = "logs/session_macro_cycle.jsonl"
MARKDOWN = "logs/session_macro_cycle.md"


def build_session_macro_cycle(
    root: Path,
    *,
    prompt_limit: int = 5,
    window_minutes: int = 20,
    write: bool = True,
) -> dict[str, Any]:
    """Build a cheap macro-cycle ledger from existing prompt and routing logs."""
    root = Path(root)
    prompts = jsonl(root / "logs" / "prompt_journal.jsonl")[-max(1, prompt_limit):]
    keys = jsonl(root / "logs" / "intent_keys.jsonl")
    cycles = group_cycles(prompts, window_minutes, max_items=prompt_limit)
    rows = [_cycle_row(root, cycle, keys) for cycle in cycles]
    manifest = manifest_freshness(root, prompts)
    latest_text = prompt_text(prompts[-1]) if prompts else ""
    latest_key = match_key(latest_text, keys) if prompts else None
    result = {
        "schema": SCHEMA,
        "ts": now(),
        "prompt_limit": prompt_limit,
        "window_minutes": window_minutes,
        "known_agent_sessions": _known_sessions(prompts),
        "cycle_count": len(rows),
        "cycles": rows,
        "latest_prompt_deleted_words": deleted_words(prompts[-1]) if prompts else [],
        "latest_prompt_shatter": shatter_prompt(latest_text, latest_key) if prompts else [],
        "manifest_freshness": manifest,
        "macro_read": _macro_read(rows, manifest),
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        write_json(root / LATEST, result)
        append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_session_macro_cycle(result), encoding="utf-8")
    return result


def render_session_macro_cycle(report: dict[str, Any]) -> str:
    lines = [
        "# Session Macro Cycle",
        "",
        f"- generated_at: `{report.get('ts', '')}`",
        f"- cycles: `{report.get('cycle_count', 0)}`",
        f"- known_sessions: `{', '.join(report.get('known_agent_sessions') or []) or 'none'}`",
        f"- read: {report.get('macro_read', '')}",
        "",
        "## Latest Prompt",
        "",
        f"- deleted_words: `{', '.join(report.get('latest_prompt_deleted_words') or []) or 'none'}`",
        "",
    ]
    for item in report.get("latest_prompt_shatter") or []:
        lines.append(f"- `{item.get('intent_key')}` -> {item.get('read')}")
    lines.extend(["", "## Cycles", ""])
    for cycle in report.get("cycles") or []:
        lines.append(f"### {cycle.get('cycle_id')} `{cycle.get('status')}` prompts `{cycle.get('prompt_count')}`")
        lines.append(f"- sessions: `{', '.join(cycle.get('session_ids') or [])}`")
        lines.append(f"- deleted_words: `{', '.join(cycle.get('deleted_words') or []) or 'none'}`")
        lines.append(f"- completion: {cycle.get('completion_read')}")
        for key in cycle.get("intent_keys") or []:
            lines.append(f"- key: `{key}`")
        lines.append("")
    fresh = report.get("manifest_freshness") or {}
    lines.extend([
        "## Manifest Freshness",
        "",
        f"- status: `{fresh.get('status', 'unknown')}`",
        f"- freshest_manifest: `{fresh.get('freshest_manifest', '')}`",
        f"- stale_manifest_count: `{fresh.get('stale_manifest_count', 0)}`",
    ])
    return "\n".join(lines) + "\n"


def _cycle_row(root: Path, cycle: list[dict[str, Any]], keys: list[dict[str, Any]]) -> dict[str, Any]:
    start = parse_ts(str(cycle[0].get("ts", "")))
    end = parse_ts(str(cycle[-1].get("ts", "")))
    matched = [match_key(prompt_text(row), keys) for row in cycle]
    shatters = [shatter_prompt(prompt_text(row), key) for row, key in zip(cycle, matched)]
    evidence = completion_evidence(root, end)
    status = "complete_enough" if evidence["score"] >= 3 else "needs_audit"
    return {
        "cycle_id": stable_id([prompt_text(row) for row in cycle]),
        "start": _iso(start),
        "end": _iso(end),
        "prompt_count": len(cycle),
        "session_ids": sorted({str(row.get("session_id") or "unknown") for row in cycle}),
        "session_ns": [row.get("session_n") for row in cycle],
        "deleted_words": unique([word for row in cycle for word in deleted_words(row)]),
        "intent_keys": [str(key.get("intent_key")) for key in matched if key],
        "prompt_shatters": shatters,
        "completion_evidence": evidence,
        "status": status,
        "completion_read": _completion_read(evidence, status),
    }


def _known_sessions(prompts: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row.get("session_id") or "unknown") for row in prompts})


def _macro_read(cycles: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    needs = sum(1 for row in cycles if row.get("status") != "complete_enough")
    freshness = manifest.get("status", "unknown")
    return f"{needs} cycle(s) need audit; manifest freshness is {freshness}."


def _completion_read(evidence: dict[str, Any], status: str) -> str:
    return f"{status}; {evidence.get('score', 0)} routing/audit artifact(s) updated after cycle end."


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value else ""


__all__ = ["build_session_macro_cycle", "render_session_macro_cycle"]
