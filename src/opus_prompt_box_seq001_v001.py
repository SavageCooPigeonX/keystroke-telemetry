"""Opus-owned Prompt Box — refined each prompt, capped, taxed.

Claude Opus is the sole writer of open problems in task_queue.json and
logs/copilot_prompt_box_latest.md. Intent-key generators and bug surfaces
only enqueue candidates; this module merges, scores, taxes, and trims.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "opus_prompt_box/v1"
MAX_OPEN_PROBLEMS = 20
TAX_HALF_LIFE_HOURS = 72.0
CANDIDATES_LOG = "logs/prompt_box_candidates.jsonl"
LATEST_JSON = "logs/opus_prompt_box_latest.json"
LATEST_MD = "logs/copilot_prompt_box_latest.md"
HISTORY_JSONL = "logs/opus_prompt_box.jsonl"

OPEN_STATUSES = {"open", "pending", "in_progress"}
DONE_STATUSES = {"done", "verified", "resolved", "closed"}
DROP_STATUS = "tax_dropped"


def refine_opus_prompt_box(
    root: Path,
    prompt: str = "",
    *,
    write: bool = True,
    max_open: int = MAX_OPEN_PROBLEMS,
) -> dict[str, Any]:
    """Merge candidates + intent routes, tax stale items, cap open problems."""
    root = Path(root)
    prompt = str(prompt or _latest_prompt(root)).strip()
    now = _now()
    intent_graph = _intent_graph(root, prompt)
    bugs = _bug_candidates(root)
    candidates = _load_candidates(root)
    absorbed = _absorb_legacy_tasks(root)
    merged = _merge_problems(prompt, intent_graph, bugs, candidates, absorbed, now)
    taxed = _apply_tax(merged, now)
    boosted = _boost_for_prompt(taxed, prompt, intent_graph)
    open_rows, dropped = _cap_open(boosted, max_open=max_open)
    done_rows = [row for row in boosted if row.get("status") in DONE_STATUSES]
    result = {
        "schema": SCHEMA,
        "ts": now,
        "writer": "claude-opus",
        "operator_prompt": prompt,
        "max_open": max_open,
        "open_count": len(open_rows),
        "dropped_count": len(dropped),
        "intent_routes": _intent_routes(intent_graph),
        "open_problems": open_rows,
        "tax_dropped": dropped,
        "done_problems": done_rows[:12],
        "routing_note": _routing_note(prompt, intent_graph, open_rows),
        "paths": {
            "latest_json": LATEST_JSON,
            "latest_md": LATEST_MD,
            "candidates": CANDIDATES_LOG,
            "task_queue": "task_queue.json",
        },
    }
    if write:
        _write_task_queue(root, open_rows + done_rows + dropped)
        _write_json(root / LATEST_JSON, result)
        _append_jsonl(root / HISTORY_JSONL, result)
        (root / LATEST_MD).write_text(render_opus_prompt_box(result), encoding="utf-8")
        _truncate_candidates(root)
    return result


def queue_prompt_box_candidate(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Non-writer surfaces call this instead of touching task_queue directly."""
    root = Path(root)
    if record.get("void"):
        return {"status": "skipped", "reason": "void"}
    candidate = {
        "ts": record.get("ts") or _now(),
        "source": record.get("source") or "intent_key_generator",
        "intent_key": record.get("intent_key", ""),
        "scope": record.get("scope", ""),
        "prompt": str(record.get("prompt") or "")[:300],
        "confidence": float(record.get("confidence") or 0.0),
        "manifest_path": record.get("manifest_path", ""),
        "intent_id": record.get("intent_id", ""),
        "kind": record.get("kind") or "intent_key",
    }
    path = root / CANDIDATES_LOG
    _append_jsonl(path, candidate)
    return {"status": "candidate", "path": str(path), "intent_key": candidate["intent_key"]}


def render_opus_prompt_box(box: dict[str, Any]) -> str:
    lines = [
        "# Opus Prompt Box",
        "",
        f"- writer: `{box.get('writer', 'claude-opus')}`",
        f"- open problems: `{box.get('open_count', 0)}` / `{box.get('max_open', MAX_OPEN_PROBLEMS)}`",
        f"- tax dropped this pass: `{box.get('dropped_count', 0)}`",
        "",
        "## Operator Prompt",
        box.get("operator_prompt") or "(none)",
        "",
        "## How Opus Routes This Prompt",
        box.get("routing_note") or "",
        "",
        "## Intent Routes",
    ]
    for row in box.get("intent_routes") or []:
        lines.append(
            f"- `{row.get('intent_key')}` domain=`{row.get('domain_id')}` "
            f"score=`{row.get('confidence', 0)}` files={len(row.get('files') or [])}"
        )
    lines.extend(["", "## Open Problems (refined this prompt)"])
    for row in box.get("open_problems") or []:
        lines.append(
            f"- `{row.get('id')}` **{row.get('title')}** "
            f"| intent=`{row.get('intent_key')}` | score=`{round(float(row.get('priority_score') or 0), 3)}` "
            f"| tax=`{round(float(row.get('tax_factor') or 1), 3)}` | hits=`{row.get('prompt_hits', 0)}`"
        )
        if row.get("focus_files"):
            lines.append(f"  - focus: {', '.join(row['focus_files'][:4])}")
    if box.get("tax_dropped"):
        lines.extend(["", "## Tax Dropped (over cap or stale)"])
        for row in box["tax_dropped"][:8]:
            lines.append(f"- `{row.get('id')}` {row.get('title')} -> {row.get('drop_reason', DROP_STATUS)}")
    return "\n".join(lines) + "\n"


def _merge_problems(
    prompt: str,
    intent_graph: dict[str, Any],
    bugs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    absorbed: list[dict[str, Any]],
    now: str,
) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in absorbed:
        key = _problem_key(row)
        by_key[key] = row
    for intent in intent_graph.get("intents") or []:
        if intent.get("void"):
            continue
        row = _problem_from_intent(intent, prompt, now)
        key = _problem_key(row)
        by_key[key] = _upsert(by_key.get(key), row, now)
    for bug in bugs:
        row = _problem_from_bug(bug, now)
        key = _problem_key(row)
        by_key[key] = _upsert(by_key.get(key), row, now)
    for cand in candidates:
        row = _problem_from_candidate(cand, now)
        key = _problem_key(row)
        by_key[key] = _upsert(by_key.get(key), row, now)
    if prompt and not by_key:
        row = _problem_from_prompt(prompt, intent_graph, now)
        by_key[_problem_key(row)] = row
    return list(by_key.values())


def _upsert(existing: dict[str, Any] | None, incoming: dict[str, Any], now: str) -> dict[str, Any]:
    if not existing:
        incoming.setdefault("created_ts", now)
        incoming.setdefault("last_refined_ts", now)
        incoming.setdefault("prompt_hits", 0)
        incoming.setdefault("status", "open")
        incoming.setdefault("writer", "claude-opus")
        return incoming
    if existing.get("status") in DONE_STATUSES:
        return existing
    existing["last_refined_ts"] = now
    existing["priority_score"] = max(
        float(existing.get("priority_score") or 0),
        float(incoming.get("priority_score") or 0),
    )
    existing["confidence"] = max(float(existing.get("confidence") or 0), float(incoming.get("confidence") or 0))
    for field in ("title", "scope", "manifest_path", "domain_id", "focus_files", "source"):
        if incoming.get(field) and not existing.get(field):
            existing[field] = incoming[field]
    files = list(dict.fromkeys([*(existing.get("focus_files") or []), *(incoming.get("focus_files") or [])]))
    existing["focus_files"] = files[:8]
    return existing


def _apply_tax(rows: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    now_dt = _parse_ts(now)
    for row in rows:
        if row.get("status") in DONE_STATUSES:
            continue
        last = _parse_ts(str(row.get("last_refined_ts") or row.get("created_ts") or now))
        hours = max(0.0, (now_dt - last).total_seconds() / 3600.0)
        tax = math.pow(0.5, hours / TAX_HALF_LIFE_HOURS)
        row["tax_factor"] = round(tax, 4)
        base = float(row.get("priority_score") or 0.1)
        row["effective_score"] = round(base * tax, 4)
    return rows


def _boost_for_prompt(
    rows: list[dict[str, Any]],
    prompt: str,
    intent_graph: dict[str, Any],
) -> list[dict[str, Any]]:
    tokens = _tokens(prompt)
    active_keys = {str(i.get("intent_key") or "") for i in intent_graph.get("intents") or []}
    for row in rows:
        if row.get("status") in DONE_STATUSES:
            continue
        overlap = len(tokens & _tokens(" ".join([row.get("title", ""), row.get("intent_key", ""), row.get("prompt", "")])))
        if row.get("intent_key") in active_keys:
            overlap += 3
        if overlap:
            row["prompt_hits"] = int(row.get("prompt_hits") or 0) + 1
            row["priority_score"] = round(min(0.99, float(row.get("priority_score") or 0.1) + overlap * 0.04), 4)
        row["effective_score"] = round(float(row.get("priority_score") or 0.1) * float(row.get("tax_factor") or 1), 4)
    return rows


def _cap_open(rows: list[dict[str, Any]], *, max_open: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    open_rows = [row for row in rows if row.get("status") in OPEN_STATUSES or row.get("status") == "pending"]
    done_rows = [row for row in rows if row.get("status") in DONE_STATUSES]
    open_rows.sort(key=lambda row: float(row.get("effective_score") or 0), reverse=True)
    kept = open_rows[:max_open]
    dropped = []
    for row in open_rows[max_open:]:
        row = dict(row)
        row["status"] = DROP_STATUS
        row["drop_reason"] = "over_cap"
        dropped.append(row)
    for row in kept:
        row["status"] = "open"
        row["writer"] = "claude-opus"
    return kept, dropped


def _intent_routes(intent_graph: dict[str, Any]) -> list[dict[str, Any]]:
    routes = []
    for intent in (intent_graph.get("intents") or [])[:12]:
        if intent.get("void"):
            continue
        routes.append({
            "intent_key": intent.get("intent_key"),
            "domain_id": intent.get("domain_id"),
            "scope": intent.get("scope"),
            "confidence": intent.get("confidence"),
            "files": [score.get("file") for score in intent.get("file_scores") or [] if score.get("file")][:6],
        })
    return routes


def _routing_note(prompt: str, intent_graph: dict[str, Any], open_rows: list[dict[str, Any]]) -> str:
    domains = list(dict.fromkeys(row.get("domain_id") for row in (intent_graph.get("intents") or []) if row.get("domain_id")))[:4]
    top = open_rows[0]["intent_key"] if open_rows else "none"
    if not prompt:
        return "No operator prompt; carrying forward taxed open problems only."
    if domains:
        return (
            f"Prompt routes through domains {', '.join(domains)}. "
            f"Primary open problem `{top}`. Opus selects intent keys, then files, then sim."
        )
    return f"Prompt lacks strong domain manifest match; holding `{top}` as provisional route."


def _problem_from_intent(intent: dict[str, Any], prompt: str, now: str) -> dict[str, Any]:
    files = [row.get("file") for row in intent.get("file_scores") or [] if row.get("file")][:6]
    return {
        "id": _next_id("pb"),
        "title": intent.get("segment") or intent.get("intent_key") or "intent move",
        "intent_key": intent.get("intent_key", ""),
        "scope": intent.get("scope", ""),
        "domain_id": intent.get("domain_id", ""),
        "prompt": prompt[:300],
        "confidence": float(intent.get("confidence") or 0.0),
        "priority_score": min(0.95, 0.35 + float(intent.get("confidence") or 0.0)),
        "focus_files": files,
        "source": "intent_graph",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 0,
    }


def _problem_from_bug(bug: dict[str, Any], now: str) -> dict[str, Any]:
    owner = str(bug.get("owner") or "repo")
    title = str(bug.get("title") or "pipeline bug")
    sev = str(bug.get("severity") or "P2").lower()
    intent_key = f"{_slug(owner)}:repair:{_slug(title)}:{sev}"
    return {
        "id": _next_id("pb"),
        "title": title,
        "intent_key": intent_key,
        "scope": owner.split("/")[0] if "/" in owner else "root",
        "domain_id": "project.keystroke_telemetry",
        "prompt": "",
        "confidence": 0.55 if sev.startswith("p0") else 0.4,
        "priority_score": 0.7 if sev.startswith("p0") else 0.45,
        "focus_files": [owner] if owner.endswith(".py") or "/" in owner else [],
        "source": bug.get("source") or "file_bug_surface",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 0,
        "bug_id": bug.get("bug_id"),
    }


def _problem_from_candidate(cand: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        "id": _next_id("pb"),
        "title": cand.get("intent_key") or cand.get("prompt") or "candidate",
        "intent_key": cand.get("intent_key", ""),
        "scope": cand.get("scope", ""),
        "prompt": cand.get("prompt", ""),
        "confidence": float(cand.get("confidence") or 0.0),
        "priority_score": min(0.9, 0.25 + float(cand.get("confidence") or 0.0)),
        "focus_files": [cand.get("manifest_path")] if cand.get("manifest_path") else [],
        "source": cand.get("source") or "candidate",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 0,
        "kind": cand.get("kind"),
    }


def _problem_from_prompt(prompt: str, intent_graph: dict[str, Any], now: str) -> dict[str, Any]:
    intent = ((intent_graph.get("intents") or [{}])[0]) if intent_graph.get("intents") else {}
    return {
        "id": _next_id("pb"),
        "title": prompt[:120],
        "intent_key": intent.get("intent_key") or f"root:route:{_slug(prompt)}:read",
        "scope": intent.get("scope") or "root",
        "prompt": prompt[:300],
        "confidence": float(intent.get("confidence") or 0.2),
        "priority_score": 0.3,
        "focus_files": [],
        "source": "operator_prompt",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 1,
    }


def _absorb_legacy_tasks(root: Path) -> list[dict[str, Any]]:
    data = _load_json(root / "task_queue.json") or {}
    tasks = data.get("tasks") if isinstance(data, dict) else []
    rows = []
    for task in tasks or []:
        if not isinstance(task, dict):
            continue
        status = str(task.get("status") or "open")
        if status in DONE_STATUSES:
            mapped = "done"
        elif status == DROP_STATUS:
            mapped = DROP_STATUS
        else:
            mapped = "open"
        rows.append({
            "id": task.get("id") or _next_id("pb"),
            "title": task.get("title") or task.get("intent") or "legacy task",
            "intent_key": task.get("intent_key", ""),
            "scope": task.get("scope", ""),
            "prompt": task.get("intent", ""),
            "confidence": float(task.get("confidence") or 0.0),
            "priority_score": _legacy_priority(task),
            "focus_files": list(task.get("focus_files") or []),
            "source": task.get("source") or "legacy_task_queue",
            "status": mapped,
            "writer": "claude-opus",
            "created_ts": task.get("created_ts") or _now(),
            "last_refined_ts": task.get("last_refined_ts") or task.get("created_ts") or _now(),
            "prompt_hits": int(task.get("prompt_hits") or 0),
        })
    return rows


def _legacy_priority(task: dict[str, Any]) -> float:
    table = {"high": 0.75, "medium": 0.5, "low": 0.3, "needs_clarity": 0.2}
    return table.get(str(task.get("priority") or ""), 0.45)


def _bug_candidates(root: Path) -> list[dict[str, Any]]:
    try:
        from src.file_bug_surface_seq001_v001 import build_file_bug_surface

        surface = build_file_bug_surface(root, write=False)
        return list(surface.get("bugs") or [])[:12]
    except Exception:
        surface = _load_json(root / "logs/file_bug_surface_latest.json") or {}
        return list(surface.get("bugs") or [])[:12]


def _intent_graph(root: Path, prompt: str) -> dict[str, Any]:
    if not prompt:
        cached = _load_json(root / "logs/intent_graph_latest.json")
        return cached if isinstance(cached, dict) else {}
    try:
        from src.tc_intent_keys_seq001_v001 import generate_intent_graph

        return generate_intent_graph(root, prompt, write=True)
    except Exception as exc:
        return {"schema": "intent_graph_error/v1", "error": str(exc), "intents": []}


def _write_task_queue(root: Path, rows: list[dict[str, Any]]) -> None:
    tasks = []
    for row in rows:
        tasks.append({
            "id": row.get("id"),
            "status": row.get("status"),
            "created_ts": row.get("created_ts"),
            "last_refined_ts": row.get("last_refined_ts"),
            "completed_ts": row.get("completed_ts"),
            "title": row.get("title"),
            "intent": row.get("prompt", "")[:300],
            "intent_key": row.get("intent_key"),
            "scope": row.get("scope"),
            "stage": "opus_prompt_box",
            "priority": _score_priority(row.get("priority_score")),
            "confidence": row.get("confidence"),
            "priority_score": row.get("priority_score"),
            "effective_score": row.get("effective_score"),
            "tax_factor": row.get("tax_factor"),
            "prompt_hits": row.get("prompt_hits"),
            "focus_files": row.get("focus_files") or [],
            "source": "opus_orchestrator",
            "writer": "claude-opus",
            "domain_id": row.get("domain_id"),
            "drop_reason": row.get("drop_reason"),
            "verification_state": "refined" if row.get("status") == "open" else row.get("status"),
        })
    _write_json(root / "task_queue.json", {"tasks": tasks, "writer": "claude-opus", "ts": _now()})


def _score_priority(score: Any) -> str:
    value = float(score or 0)
    if value >= 0.7:
        return "high"
    if value >= 0.45:
        return "medium"
    return "low"


def _truncate_candidates(root: Path) -> None:
    path = root / CANDIDATES_LOG
    if not path.exists():
        return
    path.write_text("", encoding="utf-8")


def _load_candidates(root: Path) -> list[dict[str, Any]]:
    path = root / CANDIDATES_LOG
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _problem_key(row: dict[str, Any]) -> str:
    return str(row.get("intent_key") or row.get("id") or row.get("title") or "")


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", str(text).lower()) if len(t) > 2}


def _slug(text: str) -> str:
    words = _tokens(text)
    return "_".join(sorted(words)[:4])[:48] or "work"


def _latest_prompt(root: Path) -> str:
    path = root / "logs/prompt_journal.jsonl"
    if not path.exists():
        return ""
    for line in reversed(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        return str(row.get("msg") or row.get("prompt") or "")
    return ""


def _next_id(prefix: str) -> str:
    return f"{prefix}-{int(datetime.now(timezone.utc).timestamp())}"


def _parse_ts(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
