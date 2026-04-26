"""IO helpers for thought-completer intent keys."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _priority(record: dict[str, Any]) -> str:
    if record.get("void"):
        return "needs_clarity"
    if record.get("scale") == "major" or record.get("verb") in {"refactor", "build"}:
        return "high"
    if record.get("scale") == "read":
        return "low"
    return "medium"


def _ascii(text: Any) -> str:
    return str(text).encode("ascii", errors="replace").decode("ascii")


def _next_task_id(tasks: list[dict[str, Any]]) -> str:
    nums = []
    for task in tasks:
        match = re.match(r"ik-(\d+)$", str(task.get("id", "")))
        if match:
            nums.append(int(match.group(1)))
    return f"ik-{(max(nums) if nums else 0) + 1:03d}"


def update_prompt_box(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    path = root / "task_queue.json"
    data = _load_json(path) or {"tasks": []}
    tasks = data.get("tasks") if isinstance(data, dict) and isinstance(data.get("tasks"), list) else []
    for task in tasks:
        if task.get("intent_key") == record["intent_key"] and task.get("status") != "done":
            return {"status": "duplicate", "task_id": task.get("id"), "path": str(path)}
        if task.get("intent") == record["prompt"][:300] and task.get("source") == "thought_completer_intent_keys":
            task.update({
                "title": record["intent_key"],
                "intent_key": record["intent_key"],
                "scope": record["scope"],
                "priority": _priority(record),
                "confidence": record["confidence"],
                "focus_files": [record["manifest_path"]],
                "source_key": record["intent_id"],
            })
            _write_json(path, data)
            return {"status": "updated", "task_id": task.get("id"), "path": str(path)}
    task = {
        "id": _next_task_id(tasks),
        "status": "pending",
        "created_ts": record["ts"],
        "completed_ts": None,
        "title": record["intent_key"],
        "intent": record["prompt"][:300],
        "intent_key": record["intent_key"],
        "scope": record["scope"],
        "stage": "intent_key",
        "priority": _priority(record),
        "confidence": record["confidence"],
        "focus_files": [record["manifest_path"]],
        "source": "thought_completer_intent_keys",
        "source_key": record["intent_id"],
        "verification_state": "queued",
    }
    tasks.append(task)
    data["tasks"] = tasks
    _write_json(path, data)
    return {"status": "queued", "task_id": task["id"], "path": str(path)}


def render_intent_key_block(record: dict[str, Any], managed: bool = False) -> str:
    excerpt = _ascii(record.get("manifest_excerpt", ""))[:900]
    semantic = record.get("semantic_profile") if isinstance(record.get("semantic_profile"), dict) else {}
    numeric = semantic.get("numeric_encoding") if isinstance(semantic.get("numeric_encoding"), dict) else {}
    semantic_intents = ", ".join(semantic.get("semantic_intents") or []) if semantic else ""
    matches = semantic.get("profile_matches") or [] if semantic else []
    updates = semantic.get("profile_updates") or [] if semantic else []
    lines = ["<!-- codex:intent-key-context -->"] if managed else []
    lines += [
        "## Intent Key Context",
        "",
        f"**INTENT_KEY:** `{_ascii(record['intent_key'])}`",
        f"**SCOPE:** `{_ascii(record['scope'])}`  **CONFIDENCE:** `{record['confidence']}`",
        f"**VOID:** `{record['void']}`  **WARNINGS:** {_ascii(', '.join(record['scope_warnings']) or 'none')}",
        f"**SEMANTIC_INTENTS:** `{_ascii(semantic_intents or 'none')}`",
        f"**NUMERIC_ENCODING:** `{_ascii(numeric.get('hex', 'none'))}`",
        f"**PROFILE_MATCHES:** `{_ascii(_fact_line(matches) or 'none')}`",
        f"**PROFILE_UPDATES:** `{_ascii(_fact_line(updates) or 'none')}`",
        f"**COMPLETION_HINT:** `{_ascii(semantic.get('completion_hint', '') or 'none')}`",
        f"**MANIFEST:** `{_ascii(record['manifest_path'])}`",
        "",
        "**MANIFEST_EXCERPT:**",
        "```text",
        excerpt,
        "```",
    ]
    if managed:
        lines.append("<!-- /codex:intent-key-context -->")
    return "\n".join(lines)


def _fact_line(items: list[dict[str, Any]]) -> str:
    out = []
    for item in items[:4]:
        fact_type = item.get("fact_type", "fact")
        value = item.get("value", "")
        out.append(f"{fact_type}={value}")
    return ", ".join(out)


def _replace_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _m: block, text)
    return text.rstrip() + "\n\n" + block + "\n"


def inject_copilot(root: Path, record: dict[str, Any]) -> bool:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    block = render_intent_key_block(record, managed=True)
    text = path.read_text(encoding="utf-8", errors="ignore")
    updated = _replace_block(text, "<!-- codex:intent-key-context -->", "<!-- /codex:intent-key-context -->", block)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
    return True


def write_outputs(root: Path, record: dict[str, Any], emit_prompt_box: bool, inject: bool) -> dict[str, Any]:
    logs = root / "logs"
    _write_json(logs / "intent_key_latest.json", record)
    (logs / "intent_key_context.md").write_text(render_intent_key_block(record) + "\n", encoding="utf-8")
    if emit_prompt_box and not record.get("void"):
        record["prompt_box"] = update_prompt_box(root, record)
    record["injected"] = inject_copilot(root, record) if inject else False
    _write_json(logs / "intent_key_latest.json", record)
    return record


def latest_intent_key_block(root: Path) -> str:
    record = _load_json(Path(root) / "logs" / "intent_key_latest.json")
    return render_intent_key_block(record) if isinstance(record, dict) else ""
