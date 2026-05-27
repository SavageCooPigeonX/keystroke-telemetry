"""Unified prompt brain bundle for thought-completer watcher ticks.

This is the light path for "while I am typing": assemble semantic profile,
intent key, manifest candidates, numeric/file context, and Prompt Box state
without requiring a model call.
"""
from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tc_intent_keys_seq001_v001 import generate_intent_graph, generate_intent_key
from src.tc_semantic_profile_seq001_v001 import load_profile


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_codex_compat(root: Path) -> Any | None:
    path = root / "codex_compat.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("codex_compat_prompt_brain", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prompt_box(root: Path, limit: int = 8) -> dict[str, Any]:
    data = _load_json(root / "task_queue.json", {"tasks": []})
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    open_tasks = [t for t in tasks if t.get("status") not in {"done", "verified", "resolved"}]
    return {
        "open_count": len(open_tasks),
        "tasks": [
            {
                "id": t.get("id"),
                "title": t.get("title"),
                "intent_key": t.get("intent_key"),
                "scope": t.get("scope"),
                "priority": t.get("priority"),
            }
            for t in open_tasks[-limit:]
        ],
    }


def assemble_prompt_brain(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    rewrites: list[dict[str, Any]] | None = None,
    source: str = "thought_completer",
    trigger: str = "pause",
    emit_prompt_box: bool = False,
    inject: bool = True,
    context_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    prompt = str(prompt or "").strip()
    deleted = deleted_words or []
    intent = generate_intent_key(
        root,
        prompt,
        deleted_words=deleted,
        emit_prompt_box=emit_prompt_box,
        inject=inject,
    ) if prompt else {}
    compat = _load_codex_compat(root)
    context: dict[str, Any] = context_selection or {}
    numeric_files: list[dict[str, Any]] = []
    if compat is not None and prompt and context_selection is None:
        try:
            context = compat.select_context(root, prompt, deleted, rewrites or [])
        except Exception as exc:
            context = {"status": "error", "error": str(exc), "files": []}
    if context.get("files"):
        numeric_files = list(context.get("files") or [])
    if compat is not None and prompt:
        try:
            numeric_files = compat.predict_numeric_files(root, " ".join([prompt, *deleted]))
        except Exception:
            if not numeric_files:
                numeric_files = []
    intent_graph = generate_intent_graph(
        root,
        prompt,
        deleted_words=deleted,
        limit=5,
        numeric_files=numeric_files,
        context_selection=context,
        write=True,
    ) if prompt else {}
    profile = load_profile(root)
    brain = {
        "ts": _utc_now(),
        "source": source,
        "trigger": trigger,
        "prompt": prompt,
        "deleted_words": deleted,
        "intent_key": intent.get("intent_key"),
        "intent": intent,
        "intent_graph": intent_graph,
        "semantic_profile": intent.get("semantic_profile") or _load_json(root / "logs" / "semantic_profile_latest.json", {}),
        "operator_profile": {
            "facts": profile.get("facts", {}),
            "intent_counts": profile.get("intents", {}),
        },
        "ai_fingerprint": _load_json(root / "logs" / "ai_fingerprint.json", {}),
        "context_selection": context,
        "numeric_file_encoding": numeric_files,
        "manifest_context": {
            "path": intent.get("manifest_path"),
            "confidence": intent.get("confidence"),
            "candidates": intent.get("candidates", []),
        },
        "prompt_box": _prompt_box(root),
        "paths": {
            "latest": "logs/prompt_brain_latest.json",
            "history": "logs/prompt_brain_history.jsonl",
            "context": "logs/prompt_brain_context.md",
        },
    }
    logs = root / "logs"
    _write_json(logs / "prompt_brain_latest.json", brain)
    _append_jsonl(logs / "prompt_brain_history.jsonl", brain)
    (logs / "prompt_brain_context.md").write_text(render_prompt_brain_block(brain) + "\n", encoding="utf-8")
    brain["injected"] = inject_prompt_brain(root, brain) if inject else False
    _write_json(logs / "prompt_brain_latest.json", brain)
    return brain


def render_prompt_brain_block(brain: dict[str, Any], managed: bool = False) -> str:
    semantic = brain.get("semantic_profile") or {}
    context = brain.get("context_selection") or {}
    manifest = brain.get("manifest_context") or {}
    profile = brain.get("operator_profile") or {}
    fingerprint = brain.get("ai_fingerprint") or {}
    intent_file_memory = (brain.get("intent_graph") or {}).get("intent_file_memory") or {}
    lines = ["<!-- codex:prompt-brain -->"] if managed else []
    lines += [
        "## Prompt Brain",
        "",
        f"**PROMPT:** `{_ascii(str(brain.get('prompt') or '')[:220])}`",
        f"**TRIGGER:** `{_ascii(brain.get('source'))}:{_ascii(brain.get('trigger'))}`",
        f"**INTENT_KEY:** `{_ascii(brain.get('intent_key') or 'none')}`",
        f"**INTENT_GRAPH:** `{len((brain.get('intent_graph') or {}).get('intents') or [])}` moves",
        f"**SEMANTIC:** `{_ascii(', '.join(semantic.get('semantic_intents') or []) or 'none')}`",
        f"**COMPLETION_HINT:** `{_ascii(semantic.get('completion_hint') or 'none')}`",
        f"**PROFILE_FACTS:** `{_ascii(_fact_summary(profile.get('facts') or {}))}`",
        f"**AI_FINGERPRINT:** `{_ascii((fingerprint.get('numeric_signature') or {}).get('hex', 'none'))}`",
        f"**CONTEXT_STATUS:** `{_ascii(context.get('status') or 'unknown')}` confidence `{context.get('confidence', 0)}`",
        f"**MANIFEST:** `{_ascii(manifest.get('path') or 'none')}` confidence `{manifest.get('confidence', 0)}`",
        f"**SELF_CLEARING_CONTEXT:** `{len(((brain.get('intent_graph') or {}).get('context_clearing_pass') or {}).get('context_window_files') or [])}` files",
        f"**INTENT_FILE_MEMORY:** `{intent_file_memory.get('intent_key_count', 0)}` learned keys, `{len(intent_file_memory.get('intent_keys_touched') or [])}` touched now",
        "",
        "**NUMERIC_FILES:**",
        *_file_lines(brain.get("numeric_file_encoding") or context.get("files") or []),
        "",
        "**INTENT_GRAPH_MOVES:**",
        *_intent_graph_lines((brain.get("intent_graph") or {}).get("intents") or []),
        "",
        "**FORWARD_CONTEXT_WINDOW:**",
        *_forward_context_lines(((brain.get("intent_graph") or {}).get("context_clearing_pass") or {}).get("selected_files") or []),
        "",
        f"**PROMPT_BOX_OPEN:** `{(brain.get('prompt_box') or {}).get('open_count', 0)}`",
    ]
    if managed:
        lines.append("<!-- /codex:prompt-brain -->")
    return "\n".join(lines)

def latest_prompt_brain_block(root: Path) -> str:
    brain = _load_json(Path(root) / "logs" / "prompt_brain_latest.json", {})
    return render_prompt_brain_block(brain) if isinstance(brain, dict) and brain else ""

def inject_prompt_brain(root: Path, brain: dict[str, Any]) -> bool:
    path = Path(root) / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    block = render_prompt_brain_block(brain, managed=True)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    pattern = re.compile(r"<!-- codex:prompt-brain -->.*?<!-- /codex:prompt-brain -->", re.DOTALL)
    updated = pattern.sub(block, text) if pattern.search(text) else text.rstrip() + "\n\n" + block + "\n"
    if updated != text:
        try:
            path.write_text(updated, encoding="utf-8")
        except OSError:
            return False
    return True

def _file_lines(files: list[dict[str, Any]]) -> list[str]:
    if not files:
        return ["- none"]
    return [f"- `{_ascii(f.get('name', '?'))}` score `{f.get('score', 0)}`" for f in files[:8]]

def _intent_graph_lines(intents: list[dict[str, Any]]) -> list[str]:
    if not intents:
        return ["- none"]
    lines = []
    for item in intents[:5]:
        files = ", ".join(item.get("files") or []) or "none"
        lines.append(
            f"- `{_ascii(item.get('intent_key', 'none'))}` files `{_ascii(files[:180])}`"
        )
    return lines

def _forward_context_lines(files: list[dict[str, Any]]) -> list[str]:
    if not files:
        return ["- none"]
    lines = []
    for item in files[:8]:
        reasons = "; ".join(item.get("reasons") or [])[:140]
        suffix = f" {_ascii(reasons)}" if reasons else ""
        lines.append(
            f"- `{_ascii(item.get('file', 'none'))}` score `{item.get('final_score', 0)}`{suffix}"
        )
    return lines

def _fact_summary(facts: dict[str, Any]) -> str:
    return ", ".join(f"{k}={v.get('value')}" for k, v in sorted(facts.items())) or "none"

def _ascii(value: Any) -> str:
    return str(value).encode("ascii", errors="replace").decode("ascii")
