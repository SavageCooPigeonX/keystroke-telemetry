"""Agent closeout storage for noticed bugs, fixes, and unsaid risks."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def parse_deferred_bug_arg(raw: str) -> dict[str, str]:
    parts = [part.strip() for part in str(raw or "").split("|", 2)]
    while len(parts) < 3:
        parts.append("")
    title, file_path, reason = parts[:3]
    return {"title": title or "unnamed", "file": file_path, "reason_not_fixed": reason}


def load_bug_notice_stats(root: Path) -> dict[str, Any]:
    root = Path(root)
    closeouts = _load_jsonl(root / "logs" / "agent_work_closeouts.jsonl")
    deferred = _load_jsonl(root / "logs" / "agent_deferred_bugs.jsonl")
    completed = sum(len(row.get("completed_fixes") or []) for row in closeouts)
    unsaid = sum(len(row.get("unsaid_flags") or []) for row in closeouts)
    total_noticed = len(deferred) + completed
    deferred_rate = round(len(deferred) / total_noticed, 4) if total_noticed else 0.0
    stats = {
        "schema": "agent_bug_notice_stats/v1",
        "updated_at": _now(),
        "closeout_count": len(closeouts),
        "deferred_count": len(deferred),
        "fixed_count": completed,
        "unsaid_flag_count": unsaid,
        "deferred_rate": deferred_rate,
    }
    out = root / "logs" / "agent_bug_notice_stats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    return stats


def submit_work_closeout(
    root: Path,
    *,
    note: str = "",
    files: list[str] | None = None,
    deferred_bugs: list[dict[str, str]] | None = None,
    completed_fixes: list[str] | None = None,
    unsaid_flags: list[str] | None = None,
    source: str = "codex_agent",
) -> dict[str, Any]:
    root = Path(root)
    row = {
        "schema": "agent_work_closeout/v1",
        "ts": _now(),
        "source": source,
        "note": note,
        "files": files or [],
        "deferred_bugs": deferred_bugs or [],
        "completed_fixes": completed_fixes or [],
        "unsaid_flags": unsaid_flags or [],
    }
    _append_jsonl(root / "logs" / "agent_work_closeouts.jsonl", row)
    for bug in row["deferred_bugs"]:
        _append_jsonl(
            root / "logs" / "agent_deferred_bugs.jsonl",
            {
                "schema": "agent_deferred_bug/v1",
                "ts": row["ts"],
                "source": source,
                **bug,
            },
        )
    stats = load_bug_notice_stats(root)
    return {
        "schema": "agent_work_closeout_result/v1",
        "status": "recorded",
        "closeout": row,
        "stats": stats,
    }
