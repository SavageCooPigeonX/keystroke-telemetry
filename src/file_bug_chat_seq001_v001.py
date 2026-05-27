"""Turn surfaced bugs into operator-facing file chat."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "file_bug_chat/v1"
def build_file_bug_chat(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    surface = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    syntax = _load_json(root / "logs" / "operator_syntax_triggers.json") or {}
    memory = _load_json(root / "logs" / "intent_file_memory.json") or {}
    prompts = _prompt_tail(root, 700)
    comments = [_comment(bug, syntax, memory, prompts) for bug in surface.get("bugs", [])]
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "source": "logs/file_bug_surface_latest.json",
        "comment_count": len(comments),
        "comments": comments,
        "operator_top": [f"{row['owner']}: {row['operator_comedy']}" for row in comments[:8]],
        "opus_manager_top": [f"{row['severity']} {row['intent_key']} -> {row['proposed_solution']}" for row in comments[:8]],
        "paths": {"latest": "logs/file_bug_chat_latest.json", "history": "logs/file_bug_chat.jsonl", "markdown": "logs/file_bug_chat.md"},
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "file_bug_chat_latest.json", result)
        _append_jsonl(logs / "file_bug_chat.jsonl", result)
        (logs / "file_bug_chat.md").write_text(render_file_bug_chat(result), encoding="utf-8")
    return result
def render_file_bug_chat(chat: dict[str, Any]) -> str:
    lines = ["# File Bug Chat", "", "## Operator Comedy Layer", ""]
    for line in chat.get("operator_top") or []:
        lines.append(f"- {line}")
    lines.extend(["", "## Opus Manager Layer", ""])
    for line in chat.get("opus_manager_top") or []:
        lines.append(f"- {line}")
    lines.extend(["", "## File Comments", ""])
    for row in chat.get("comments") or []:
        lines.extend([
            f"### {row.get('owner')}",
            "",
            f"**Operator:** {row.get('operator_comedy')}",
            "",
            f"**Coding Agent:** {row.get('coding_agent_note', '')}",
            "",
            f"**Opus:** {row.get('opus_manager_note')}",
            "",
            f"- intent_key: `{row.get('intent_key')}`",
            f"- interlink_score: `{row.get('interlink_score')}/10`",
            f"- learned_from_sim: {row.get('learned_from_sim')}",
            f"- proposed_solution: {row.get('proposed_solution')}",
            f"- high_coupling_note: {row.get('high_coupling_note')}",
            f"- past_prompt_traces: {', '.join(row.get('past_prompt_traces') or []) or 'none'}",
            "",
        ])
    return "\n".join(lines)
def _comment(bug: dict[str, Any], syntax: dict[str, Any], memory: dict[str, Any], prompts: list[dict[str, Any]]) -> dict[str, Any]:
    owner = str(bug.get("owner") or "unknown")
    intent_key = _intent_key(bug)
    traces = _prompt_traces(owner, bug, prompts)
    learned = _learned(owner, syntax, memory)
    role = _sim_role(bug)
    score, checks = _interlink_score(bug, learned, traces)
    proposed = str(bug.get("next_action") or "route to orchestrator")
    evidence = str(bug.get("evidence") or "")
    operator = f"I keep getting touched because {bug.get('title')}. I am in this sim because I help {role}. My evidence is {evidence}. My proposed fix is: {proposed}."
    opus = f"{bug.get('severity')} owner={owner}; source={bug.get('source')}; intent_key={intent_key}; action={proposed}; checks={','.join(checks)}"
    coding = f"Check `{owner}` through `{intent_key}`. Verify this evidence first: {evidence}. Then do: {proposed}. Keep the patch bounded and write the closeout receipt to the local manifest plus ROOT_SIM_KEYS.md."
    return {
        "bug_id": bug.get("bug_id"),
        "owner": owner,
        "severity": bug.get("severity"),
        "intent_key": intent_key,
        "operator_comedy": operator,
        "operator_note": operator,
        "coding_agent_note": coding,
        "opus_manager_note": opus,
        "why_touched": bug.get("title", ""),
        "sim_role": role,
        "past_prompt_traces": traces,
        "learned_from_sim": learned,
        "interlink_score": score,
        "interlink_questions_passed": checks,
        "proposed_solution": proposed,
        "high_coupling_note": _coupling_note(bug),
        "final_note": "Write the receipt into the folder manifest, then let Opus decide whether this becomes a debug chain.",
    }
def _intent_key(bug: dict[str, Any]) -> str:
    owner = _slug(str(bug.get("owner") or "repo"))
    title = _slug(str(bug.get("title") or "repair"))
    sev = str(bug.get("severity") or "p").lower()
    return f"{owner}:repair:{title}:{sev}"
def _sim_role(bug: dict[str, Any]) -> str:
    bid = str(bug.get("bug_id") or "")
    owner = str(bug.get("owner") or "")
    if "deepseek" in bid or "deepseek" in owner:
        return "closing DeepSeek job/result receipts"
    if "edit_pairs" in bid:
        return "teaching prompts which edits actually happened"
    if "cognition" in bid:
        return "keeping operator intent labels usable"
    if "compliance" in bid:
        return "turning compiler warnings into bounded repair jobs"
    if "dead_stale" in bid:
        return "promoting stale suspects into debug chains"
    return "making file pressure visible to the master manifest"
def _learned(owner: str, syntax: dict[str, Any], memory: dict[str, Any]) -> str:
    files = syntax.get("files") or {}
    if owner in files:
        row = files[owner]
        tokens = ", ".join((row.get("learned_operator_tokens") or [])[:8]) or "none"
        return f"observations={row.get('observations', 0)} learned_tokens={tokens}"
    hits = []
    for record in (memory.get("intent_keys") or {}).values():
        if owner in (record.get("dominant_files") or []):
            hits.append(record.get("intent_key", ""))
    if hits:
        return "dominant in intent keys: " + ", ".join(hits[:3])
    return "no direct learned file memory yet; using bug surface evidence as first training trace"
def _prompt_traces(owner: str, bug: dict[str, Any], prompts: list[dict[str, Any]]) -> list[str]:
    tokens = set(_tokens(" ".join([owner, str(bug.get("title", "")), str(bug.get("evidence", ""))]))) - {"logs", "json", "latest"}
    hits = []
    for row in reversed(prompts):
        text = str(row.get("prompt") or row.get("msg") or row.get("text") or "")
        if tokens and tokens & set(_tokens(text)):
            session = row.get("session") or row.get("session_n") or row.get("idx") or "?"
            hits.append(f"{session}:{text[:70]}")
        if len(hits) >= 3:
            break
    return hits
def _interlink_score(bug: dict[str, Any], learned: str, traces: list[str]) -> tuple[int, list[str]]:
    checks = []
    for key in ("owner", "severity", "source", "evidence", "next_action"):
        if bug.get(key):
            checks.append(key)
    if "no direct" not in learned:
        checks.append("learned_memory")
    if traces:
        checks.append("prompt_trace")
    if bug.get("bug_id"):
        checks.append("intent_key_basis")
    if "deps=" in str(bug.get("evidence", "")):
        checks.append("coupling_context")
    if "stale" in str(bug.get("title", "")):
        checks.append("staleness_context")
    return min(10, len(checks)), checks[:10]
def _coupling_note(bug: dict[str, Any]) -> str:
    evidence = str(bug.get("evidence") or "")
    if "deps=" in evidence:
        return "Previously breaks when downstream queues drift; keep dependency receipts fresh before trusting this file."
    if "stale" in str(bug.get("title", "")):
        return "Do not create more jobs until this lane has a receipt/expiry rule."
    if "warnings=" in evidence:
        return "Compiler pressure accumulates when warnings stay advisory; sample owners before broad rewrites."
    return "No high-coupling warning found; keep this as a local manifest receipt."
def _prompt_tail(root: Path, limit: int) -> list[dict[str, Any]]:
    path = root / "logs" / "prompt_journal.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows
def _tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-zA-Z0-9]+", text.lower().replace("_", " ")) if len(tok) > 2]
def _slug(text: str) -> str:
    return "_".join(_tokens(text)[:5]) or "repo"
def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
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
