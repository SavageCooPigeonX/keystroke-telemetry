"""Source collectors for the intent overlay bridge."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENT_SCHEMA = "intent_overlay_event/v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path, limit: int = 2000) -> list[dict[str, Any]]:
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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def canonical_intent_key(intent_key: str) -> str:
    parts = [
        re.sub(r"[^a-z0-9_./-]+", "_", part.lower()).strip("_")
        for part in str(intent_key or "").split(":")
    ]
    parts = [part for part in parts if part]
    return ":".join(parts[:4]) if parts else ""


def _tokens(text: str) -> set[str]:
    return {
        tok for tok in re.findall(r"[a-zA-Z0-9_]+", str(text or "").lower())
        if len(tok) > 2
    }


def _verb(text: str) -> str:
    tokens = _tokens(text)
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
    why = " ".join(str(row.get(k) or "") for k in ("edit_why", "prompt_msg", "reason"))
    scale = "patch" if int(row.get("added") or 0) or int(row.get("removed") or 0) else "minor"
    return f"{scope}:{_verb(why)}:{Path(file_path).stem or 'unknown'}:{scale}"


def collect_operator_events(root: Path) -> list[dict[str, Any]]:
    events = []
    for row in load_jsonl(root / "logs" / "intent_keys.jsonl"):
        intent_key = canonical_intent_key(str(row.get("intent_key") or ""))
        if intent_key:
            events.append({
                "schema": EVENT_SCHEMA,
                "ts": row.get("ts") or now_iso(),
                "intent_key": intent_key,
                "source": "operator_prompt",
                "pass": "forward",
                "prompt": row.get("prompt", ""),
                "files": [row.get("manifest_path")] if row.get("manifest_path") else [],
                "evidence": [{"type": "intent_key_row", "confidence": row.get("confidence", 0)}],
            })
    return events


def collect_edit_events(root: Path) -> list[dict[str, Any]]:
    events = []
    for row in load_jsonl(root / "logs" / "edit_pairs.jsonl"):
        intent_key = canonical_intent_key(infer_intent_key_from_edit(row))
        if not intent_key:
            continue
        source = str(row.get("source") or row.get("edit_author") or "agent_edit")
        events.append({
            "schema": EVENT_SCHEMA,
            "ts": row.get("edit_ts") or row.get("ts") or now_iso(),
            "intent_key": intent_key,
            "source": "agent_edit" if source in {"codex", "copilot", "cursor", "unknown"} else source,
            "pass": "backward",
            "prompt": row.get("prompt_msg", ""),
            "files": [row.get("file")] if row.get("file") else [],
            "attempt_id": row.get("edit_hash") or row.get("response_id") or "",
            "evidence": [{"type": "edit_pair", "match_score": row.get("match_score", 0)}],
        })
    return events


def collect_outcome_events(root: Path) -> list[dict[str, Any]]:
    events = []
    status_map = {"strengthen_path": "solved", "keep_watch": "partial", "weaken_path": "failed"}
    for row in load_jsonl(root / "logs" / "file_solution_outcomes.jsonl"):
        intent_key = canonical_intent_key(infer_intent_key_from_edit(row))
        if not intent_key:
            continue
        score = row.get("outcome_score") if isinstance(row.get("outcome_score"), dict) else {}
        verdict = str(score.get("verdict") or "keep_watch")
        events.append({
            "schema": EVENT_SCHEMA,
            "ts": row.get("ts") or now_iso(),
            "intent_key": intent_key,
            "source": "outcome_score",
            "pass": "backward",
            "status": status_map.get(verdict, "partial"),
            "files": [row.get("file")] if row.get("file") else [],
            "attempt_id": row.get("commit") or "",
            "outcome_score": score,
            "evidence": [{"type": "solution_outcome", "verdict": verdict}],
        })
    return events


def collect_overlay_events(root: Path) -> list[dict[str, Any]]:
    events = [
        *collect_operator_events(root),
        *collect_edit_events(root),
        *collect_outcome_events(root),
    ]
    return sorted(events, key=lambda row: str(row.get("ts") or ""))
