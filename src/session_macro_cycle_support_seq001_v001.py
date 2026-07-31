"""Support helpers for session macro-cycle grouping."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_NAMES = {
    "dynamic_context_pack.json",
    "context_selection.json",
    "intent_graph_latest.json",
    "intent_key_latest.json",
    "file_self_sim_learning_latest.json",
    "file_manifest_state_sync_latest.json",
    "push_manifest_refresh_latest.json",
    "operator_intent_888.json",
    "opus_orchestrator_runtime_latest.json",
}


def completion_evidence(root: Path, after: datetime | None) -> dict[str, Any]:
    logs = root / "logs"
    rows = []
    if logs.exists():
        for name in AUDIT_LOG_NAMES:
            path = logs / name
            if path.exists():
                mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
                rows.append({
                    "path": f"logs/{name}",
                    "updated_at": mtime.isoformat(),
                    "after_cycle": bool(after and mtime >= after),
                })
    return {"score": sum(1 for row in rows if row["after_cycle"]), "artifacts_after_cycle": rows}


def manifest_freshness(root: Path, prompts: list[dict[str, Any]]) -> dict[str, Any]:
    latest_prompt = parse_ts(str(prompts[-1].get("ts", ""))) if prompts else None
    rows = []
    for path in root.rglob("MANIFEST.md"):
        if ".git" in path.parts:
            continue
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except OSError:
            continue
        rows.append({"path": rel(root, path), "updated_at": mtime.isoformat(), "after_latest_prompt": bool(latest_prompt and mtime >= latest_prompt)})
    rows.sort(key=lambda row: row["updated_at"], reverse=True)
    fresh = [row for row in rows if row["after_latest_prompt"]]
    return {
        "status": "fresh_after_latest_prompt" if fresh else "no_manifest_update_after_latest_prompt",
        "freshest_manifest": rows[0]["path"] if rows else "",
        "freshest_updated_at": rows[0]["updated_at"] if rows else "",
        "fresh_after_latest_prompt_count": len(fresh),
        "stale_manifest_count": max(0, len(rows) - len(fresh)),
        "sample": rows[:8],
    }


def group_cycles(prompts: list[dict[str, Any]], window_minutes: int, max_items: int) -> list[list[dict[str, Any]]]:
    cycles: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    last_ts: datetime | None = None
    for row in prompts:
        ts = parse_ts(str(row.get("ts", "")))
        gap = ((ts - last_ts).total_seconds() / 60.0) if ts and last_ts else 0
        if current and (gap > window_minutes or len(current) >= max_items):
            cycles.append(current)
            current = []
        current.append(row)
        last_ts = ts or last_ts
    if current:
        cycles.append(current)
    return cycles


def shatter_prompt(prompt: str, key: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    clauses = [part.strip(" -") for part in re.split(r"\s+-\s+|[.;?]\s+", prompt) if part.strip(" -")]
    out = []
    for clause in clauses[:8]:
        semantic = semantic_bucket(clause)
        seed_key = str(key.get("intent_key")) if key and key.get("intent_key") else f"root:route:{slug(clause)}:minor"
        out.append({"intent_key": seed_key, "semantic_intent": semantic, "encoding": encoding(semantic, clause, seed_key), "read": clause[:180]})
    return out


def semantic_bucket(text: str) -> str:
    low = text.lower()
    checks = [
        ("session_macro_cycle", ("session", "macro", "last 5", "grouping", "cycle")),
        ("thought_completion", ("thought completer", "deleted words", "pause")),
        ("intent_key_extraction", ("intent key", "shatter", "encoding", "numeric", "neumeric")),
        ("file_sim_orchestration", ("file sim", "sim orchestrator", "context select")),
        ("manifest_state", ("manifest", "folder", "master")),
        ("agent_execution_audit", ("codex", "copilot", "work complete", "auditor")),
    ]
    for name, words in checks:
        if any(word in low for word in words):
            return name
    return "unknown"


def encoding(semantic: str, text: str, intent_key: str) -> dict[str, Any]:
    digest = hashlib.sha256(f"{semantic}|{text[:160]}|{intent_key}".encode("utf-8")).digest()
    vector = [int.from_bytes(digest[i:i + 2], "big") for i in range(0, 24, 2)]
    return {"algorithm": "sha256_u16_v1", "vector": vector, "hex": digest[:12].hex()}


def match_key(prompt: str, keys: list[dict[str, Any]]) -> dict[str, Any] | None:
    norm = norm_tokens(prompt)
    best, score = None, 0.0
    for row in reversed(keys):
        overlap = token_overlap(norm, norm_tokens(str(row.get("prompt") or "")))
        if overlap > score:
            best, score = row, overlap
    return best if score >= 0.68 else None


def prompt_text(row: dict[str, Any]) -> str:
    return str(row.get("msg") or row.get("final_text") or "")


def deleted_words(row: dict[str, Any]) -> list[str]:
    words = row.get("deleted_words") or []
    if words and isinstance(words[0], dict):
        return [str(item.get("word") or "") for item in words if item.get("word")]
    return [str(word) for word in words if str(word)]


def jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def norm_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def token_overlap(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, len(a | b))


def slug(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:4]
    return "_".join(words) or "prompt"


def stable_id(parts: list[str]) -> str:
    return "cycle-" + hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def unique(values: list[str]) -> list[str]:
    seen, out = set(), []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
