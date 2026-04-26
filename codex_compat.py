"""Codex compatibility adapter for local logging and training pairs.

This module deliberately does not install keyboard hooks or read the clipboard.
It bridges explicit Codex/session events into the existing repo logs:

    logs/prompt_journal.jsonl
    logs/ai_responses.jsonl
    logs/edit_pairs.jsonl
    logs/training_pairs.jsonl

Usage examples:
    py codex_compat.py log-prompt --prompt "fix the parser"
    py codex_compat.py log-response --prompt "fix the parser" --response "patched parser.py"
    py codex_compat.py log-edit --file src/parser.py --why "fix parser edge case"
    py codex_compat.py capture-pair
    py codex_compat.py import-jsonl path/to/codex-session.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _words(text: str) -> list[str]:
    return [part.strip(".,;:!?()[]{}\"'`") for part in str(text).split() if part.strip(".,;:!?()[]{}\"'`")]


def _parse_deleted_words(deleted_words: list[Any] | None = None, deleted_text: str = "") -> list[str]:
    words: list[str] = []
    for item in deleted_words or []:
        if isinstance(item, dict):
            text = item.get("word") or item.get("text") or item.get("deleted") or item.get("value") or ""
        else:
            text = str(item)
        words.extend(_words(text))
    words.extend(_words(deleted_text))
    seen = set()
    unique = []
    for word in words:
        key = word.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(word)
    return unique[:30]


def _state_from_deletions(deletion_ratio: float, hesitation_count: int = 0) -> str:
    if deletion_ratio > 0.4 or hesitation_count > 5:
        return "frustrated"
    if deletion_ratio > 0.2 or hesitation_count > 2:
        return "hesitant"
    if deletion_ratio > 0:
        return "neutral"
    return "unknown"


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_text_resilient(path: Path, text: str) -> None:
    """Write text in a way that tolerates OneDrive/Windows target-file quirks."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        if tmp.exists():
            tmp.unlink()
        with path.open("r+", encoding="utf-8", errors="ignore", newline="") as handle:
            handle.seek(0)
            handle.write(text)
            handle.truncate()


def _load_jsonl_tail(path: Path, max_lines: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _load_entropy_module() -> Any | None:
    module_path = _repo_root() / "src" / "entropy_shedding_seq001_v001.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("codex_entropy_shedding", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_status(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _refresh_entropy(root: Path) -> dict[str, Any]:
    entropy = _load_entropy_module()
    if entropy is None:
        return {"status": "missing"}
    try:
        data = entropy.accumulate_entropy(root)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    if isinstance(data, dict) and "error" in data:
        return {"status": "unavailable", "error": data.get("error")}
    try:
        block = entropy.build_entropy_block(root)
    except Exception as exc:
        block = f"<!-- entropy unavailable: {exc} -->"
    block_path = root / "logs" / "codex_entropy_block.md"
    block_path.parent.mkdir(parents=True, exist_ok=True)
    block_path.write_text(block or "<!-- pigeon:entropy-map -->\nNo entropy data yet.\n<!-- /pigeon:entropy-map -->\n", encoding="utf-8")
    return {
        "status": "ok",
        "block_path": str(block_path),
        "global_avg_entropy": data.get("global_avg_entropy"),
        "tracked_modules": data.get("tracked_modules"),
        "top_entropy_modules": data.get("top_entropy_modules", [])[:5],
    }


def _load_intent_reconstructor() -> Any | None:
    module_path = _repo_root() / "src" / "intent_reconstructor_seq001_v001.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("codex_intent_reconstructor", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_context_select_agent() -> Any | None:
    src_dir = _repo_root() / "src"
    matches = sorted(src_dir.glob("context_select_agent_seq001*.py"), key=lambda item: item.name)
    for module_path in matches:
        spec = importlib.util.spec_from_file_location("codex_context_select_agent", module_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "run_assembly"):
            return module
    return None


def _load_intent_numeric(root: Path) -> Any | None:
    src_dir = _repo_root() / "src"
    matches = sorted(src_dir.glob("intent_numeric_seq001*.py"), key=lambda item: item.name)
    for module_path in matches:
        spec = importlib.util.spec_from_file_location("codex_intent_numeric", module_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT = Path(root)
        module.VOCAB_PATH = Path(root) / "logs" / "intent_vocab.json"
        module.MATRIX_PATH = Path(root) / "logs" / "intent_matrix.json"
        module.TOUCH_LOG_PATH = Path(root) / "logs" / "intent_touches.jsonl"
        module._vocab = {}
        module._vocab_inverse = {}
        module._next_id = 1
        module._vocab_loaded = False
        module._matrix = {}
        module._touch_counts = {}
        module._matrix_loaded = False
        module._surface_healed = False
        module._lexicon_cache = None
        return module
    return None


def train_numeric_surface(root: Path, prompt: str, files: list[str]) -> dict[str, Any]:
    root = Path(root)
    numeric = _load_intent_numeric(root)
    if numeric is None:
        return {"status": "missing", "files": files}
    try:
        numeric.record_touch(prompt, files)
        stats = numeric.get_stats()
        result = {
            "status": "ok",
            "files": files,
            "vocab_size": stats.get("vocab_size", 0),
            "files_tracked": stats.get("files_tracked", 0),
            "total_touches": stats.get("total_touches", 0),
        }
    except Exception as exc:
        result = {"status": "error", "error": str(exc), "files": files}
    _append_jsonl(root / "logs" / "numeric_training_history.jsonl", result)
    return result


def predict_numeric_files(root: Path, prompt: str, top_n: int = 6) -> list[dict[str, Any]]:
    root = Path(root)
    numeric = _load_intent_numeric(root)
    if numeric is None:
        return []
    try:
        return [
            {"name": name, "score": score}
            for name, score in numeric.predict_files(prompt, top_n=top_n)
        ]
    except Exception:
        return []


def _run_sim_buffer(root: Path, buffer: str, timeout_s: int = 45) -> dict[str, Any]:
    """Run the existing thought-completer sim path for a buffer.

    This is intentionally subprocess-based because the sim module has package
    imports and global paths tuned for the repo runtime.
    """
    if not buffer.strip():
        return {"status": "skipped", "reason": "empty_buffer"}
    script = root / "src" / "thought_completer.py"
    if not script.exists():
        return {"status": "missing", "reason": str(script)}
    try:
        result = subprocess.run(
            ["py", str(script), "--sim-buffer", buffer],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "timeout_s": timeout_s,
            "stdout": (exc.stdout or "")[-2000:],
            "stderr": (exc.stderr or "")[-2000:],
        }
    except OSError as exc:
        return {"status": "error", "error": str(exc)}

    return {
        "status": "ok" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def _latest_json(path: Path) -> dict[str, Any] | None:
    rows = _load_jsonl_tail(path, max_lines=1)
    return rows[-1] if rows else None


def _replace_managed_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _match: block, text)
    return text.rstrip() + "\n\n" + block + "\n"


def _render_pre_prompt_block(state: dict[str, Any]) -> str:
    context = state.get("context_selection") or {}
    composition = state.get("composition") or {}
    sim = state.get("sim") or {}
    files = context.get("files") or []
    deleted_words = _parse_deleted_words(composition.get("deleted_words") or [], composition.get("deleted_text", ""))

    lines = [
        "<!-- codex:pre-prompt-state -->",
        "## Codex Pre-Prompt State",
        "",
        f"*Prepared {state.get('ts', '')} before model handoff*",
        "",
        f"**PROMPT:** `{state.get('final_text', '')[:220]}`",
        "",
        f"**DELETION_RATIO:** `{composition.get('deletion_ratio', 0)}`",
        f"**DELETED_WORDS:** {', '.join(deleted_words[:12]) if deleted_words else 'none'}",
        f"**HESITATION_COUNT:** `{state.get('hesitation_count', 0)}`",
        "",
        "**NUMERIC_CONTEXT:**",
    ]
    if files:
        for file_ref in files[:8]:
            lines.append(f"- `{file_ref.get('name', '?')}` score={file_ref.get('score', 0)}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        f"**HANDOFF_READY:** `{state.get('handoff_ready', False)}`",
        f"**SIM_STATUS:** `{sim.get('status', 'not_run')}`",
    ])
    if state.get("block_reason"):
        lines.append(f"**BLOCK_REASON:** {state['block_reason']}")
    sim_tail = (sim.get("stdout") or "").strip().splitlines()[-8:]
    if sim_tail:
        lines.append("**SIM_OUTPUT:**")
        lines.extend(f"- {line[:180]}" for line in sim_tail)

    unsaid = composition.get("unsaid_reconstruction")
    if unsaid:
        lines.extend(["", f"**UNSAID_RECONSTRUCTION:** {unsaid[:400]}"])

    lines.append("<!-- /codex:pre-prompt-state -->")
    return "\n".join(lines)


def _inject_pre_prompt_state(root: Path, state: dict[str, Any]) -> bool:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    block = _render_pre_prompt_block(state)
    updated = _replace_managed_block(
        text,
        "<!-- codex:pre-prompt-state -->",
        "<!-- /codex:pre-prompt-state -->",
        block,
    )
    if updated != text:
        _write_text_resilient(path, updated)
    return True


def _inject_dynamic_context_pack(root: Path, pack: dict[str, Any]) -> bool:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    block = _render_dynamic_context_pack(pack, managed=True)
    updated = _replace_managed_block(
        text,
        "<!-- codex:dynamic-context-pack -->",
        "<!-- /codex:dynamic-context-pack -->",
        block,
    )
    if updated != text:
        _write_text_resilient(path, updated)
    return True


def _running_prompt_summary(root: Path) -> dict[str, Any]:
    prompts = _load_jsonl_tail(root / "logs" / "prompt_journal.jsonl", max_lines=250)
    if not prompts:
        return {
            "total_prompts": 0,
            "avg_del_ratio": 0,
            "dominant_state": "unknown",
            "state_distribution": {},
        }
    del_ratios: list[float] = []
    states: dict[str, int] = {}
    for row in prompts:
        signals = row.get("signals") if isinstance(row.get("signals"), dict) else {}
        try:
            del_ratios.append(float(signals.get("deletion_ratio", row.get("deletion_ratio", 0)) or 0))
        except Exception:
            pass
        state = str(row.get("cognitive_state") or signals.get("cognitive_state") or "unknown")
        states[state] = states.get(state, 0) + 1
    dominant = max(states.items(), key=lambda item: item[1])[0] if states else "unknown"
    avg_del = round(sum(del_ratios) / max(len(del_ratios), 1), 3)
    return {
        "total_prompts": len(prompts),
        "avg_del_ratio": avg_del,
        "dominant_state": dominant,
        "state_distribution": states,
    }


def _task_queue_summary(root: Path) -> dict[str, Any]:
    resolver = _load_json(root / "logs" / "codex_intent_resolver.json") or {}
    intents = resolver.get("intents") if isinstance(resolver.get("intents"), list) else []
    unresolved = [i for i in intents if i.get("status") not in {"done", "resolved"}]
    in_progress = [i for i in unresolved if i.get("status") == "partial"]
    return {
        "total": len(intents),
        "in_progress": [str(i.get("task") or i.get("source_key") or i.get("ts") or "") for i in in_progress[:8]],
        "pending": len(unresolved),
        "done": len(intents) - len(unresolved),
    }


def _build_live_prompt_telemetry(root: Path, pack: dict[str, Any]) -> dict[str, Any]:
    signals = pack.get("signals") if isinstance(pack.get("signals"), dict) else {}
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    focus_files = pack.get("focus_files") if isinstance(pack.get("focus_files"), list) else []
    prompt_text = str(pack.get("prompt") or "")
    ts = str(pack.get("ts") or _utc_now())
    deleted_words = _parse_deleted_words(signals.get("deleted_words") if isinstance(signals.get("deleted_words"), list) else [], "")
    deepseek_job = pack.get("deepseek_job") if isinstance(pack.get("deepseek_job"), dict) else {}
    return {
        "schema": "prompt_telemetry/latest/v2",
        "updated_at": _utc_now(),
        "source": "codex_compat.dynamic_context_pack",
        "latest_prompt": {
            "session_n": None,
            "ts": ts,
            "chars": len(prompt_text),
            "preview": prompt_text[:240],
            "intent": context.get("intent_keys", prompt_text)[:240],
            "state": signals.get("cognitive_state") or "unknown",
            "files_open": [str(item.get("name")) for item in focus_files[:12] if isinstance(item, dict) and item.get("name")],
            "module_refs": [str(item.get("name")) for item in focus_files[:12] if isinstance(item, dict) and item.get("reason") == "numeric_context"],
        },
        "signals": {
            "wpm": 0,
            "chars_per_sec": 0,
            "deletion_ratio": signals.get("deletion_ratio", 0),
            "intent_deletion_ratio": signals.get("intent_deletion_ratio", 0),
            "hesitation_count": signals.get("hesitation_count", 0),
            "rewrite_count": 0,
            "typo_corrections": 0,
            "intentional_deletions": len(deleted_words),
            "total_keystrokes": max(len(prompt_text) + sum(len(w) for w in deleted_words), 0),
            "duration_ms": signals.get("duration_ms", 0),
        },
        "composition_binding": {
            "matched": True,
            "source": str(pack.get("surface") or "codex"),
            "age_ms": 0,
            "key": str(deepseek_job.get("job_id") or ""),
            "match_score": context.get("confidence", 0),
        },
        "deleted_words": deleted_words,
        "rewrites": [],
        "task_queue": _task_queue_summary(root),
        "hot_modules": [str(item.get("name")) for item in focus_files[:8] if isinstance(item, dict) and item.get("name")],
        "running_summary": _running_prompt_summary(root),
        "deepseek": {
            "model": deepseek_job.get("model") or _deepseek_default_model(),
            "job_id": deepseek_job.get("job_id") or "",
            "status": deepseek_job.get("status") or "not_queued",
            "autonomous_write": bool(deepseek_job.get("autonomous_write")),
        },
        "staleness": {
            "replaces_legacy_pigeon_prompt_telemetry": True,
            "fresh_source": "logs/dynamic_context_pack.json",
        },
    }


def _render_prompt_telemetry_block(telemetry: dict[str, Any]) -> str:
    return "\n".join([
        "<!-- pigeon:prompt-telemetry -->",
        "## Live Prompt Telemetry",
        "",
        f"*Auto-updated {telemetry.get('updated_at', '')} - source: `logs/prompt_telemetry_latest.json`*",
        "",
        "Use this block as the highest-freshness prompt-level telemetry. It is generated from Codex live context, not the stale legacy daemon.",
        "",
        "```json",
        json.dumps(telemetry, indent=2, ensure_ascii=False),
        "```",
        "",
        "<!-- /pigeon:prompt-telemetry -->",
    ])


def _write_live_prompt_telemetry(root: Path, pack: dict[str, Any]) -> dict[str, Any]:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    telemetry = _build_live_prompt_telemetry(root, pack)
    (logs / "prompt_telemetry_latest.json").write_text(
        json.dumps(telemetry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    path = root / ".github" / "copilot-instructions.md"
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = _replace_managed_block(
            text,
            "<!-- pigeon:prompt-telemetry -->",
            "<!-- /pigeon:prompt-telemetry -->",
            _render_prompt_telemetry_block(telemetry),
        )
        if updated != text:
            _write_text_resilient(path, updated)
    return telemetry


def _render_current_query_block(pack: dict[str, Any]) -> str:
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    signals = pack.get("signals") if isinstance(pack.get("signals"), dict) else {}
    files = context.get("files") if isinstance(context.get("files"), list) else []
    file_names = [str(item.get("name")) for item in files if isinstance(item, dict) and item.get("name")]
    stale_blocks = [
        str(item) for item in (context.get("stale_blocks") or [])
        if str(item) not in {"current-query", "prompt-telemetry"}
    ]
    deleted = _parse_deleted_words(signals.get("deleted_words") if isinstance(signals.get("deleted_words"), list) else [], "")
    deepseek = pack.get("deepseek_job") if isinstance(pack.get("deepseek_job"), dict) else {}
    lines = [
        "<!-- pigeon:current-query -->",
        "## What You Actually Mean Right Now",
        "",
        f"*Assembled {pack.get('ts', '')} - codex_compat dynamic context - zero LLM calls*",
        "",
        f"**INTENT KEYS:** `{context.get('intent_keys') or pack.get('prompt') or ''}`",
        "",
        f"**FILES:** {', '.join(file_names[:8]) if file_names else 'none'}",
        "",
        f"**LEGACY_STALE_BLOCKS:** {', '.join(stale_blocks) if stale_blocks else 'none'}",
        "",
        f"**LIVE_REPLACEMENTS:** dynamic-context-pack, prompt-telemetry/latest/v2, DeepSeek V4 job `{deepseek.get('job_id', '')}`",
        "",
        f"**DELETED WORDS:** {', '.join(deleted) if deleted else 'none'}",
        "",
        f"**COGNITIVE STATE:** `{signals.get('cognitive_state') or 'unknown'}`",
        "<!-- /pigeon:current-query -->",
    ]
    return "\n".join(lines)


def _render_staleness_alert_block(pack: dict[str, Any], telemetry: dict[str, Any]) -> str:
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    stale_blocks = [
        str(item) for item in (context.get("stale_blocks") or [])
        if str(item) not in {"current-query", "prompt-telemetry"}
    ]
    lines = [
        "<!-- pigeon:staleness-alert -->",
        "## Staleness Alert",
        "",
        f"*Checked {telemetry.get('updated_at', '')} - Codex live context refreshed*",
        "",
        "**Live replacements active:** `pigeon:current-query`, `pigeon:prompt-telemetry`, `codex:dynamic-context-pack`, DeepSeek V4 prompt queue.",
        "",
        f"**Legacy stale blocks still reported:** {', '.join(stale_blocks) if stale_blocks else 'none'}",
        "",
        "**Rule:** Prefer the Codex live blocks below over older commit-time or daemon-time sections.",
        "<!-- /pigeon:staleness-alert -->",
    ]
    return "\n".join(lines)


def _write_copilot_live_query_blocks(root: Path, pack: dict[str, Any], telemetry: dict[str, Any]) -> None:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    updated = _replace_managed_block(
        text,
        "<!-- pigeon:current-query -->",
        "<!-- /pigeon:current-query -->",
        _render_current_query_block(pack),
    )
    updated = _replace_managed_block(
        updated,
        "<!-- pigeon:staleness-alert -->",
        "<!-- /pigeon:staleness-alert -->",
        _render_staleness_alert_block(pack, telemetry),
    )
    if updated != text:
        _write_text_resilient(path, updated)


def _surface_activity(root: Path) -> dict[str, Any]:
    logs = root / "logs"
    uia_rows = _load_jsonl_tail(logs / "uia_live.jsonl", max_lines=200)
    key_rows = _load_jsonl_tail(logs / "os_keystrokes.jsonl", max_lines=200)

    latest_switch = None
    for row in reversed(uia_rows):
        if row.get("event") == "context_switch":
            latest_switch = {
                "ts": row.get("ts"),
                "from": row.get("from"),
                "to": row.get("to"),
                "name": row.get("name"),
                "class": row.get("class"),
                "auto_id": row.get("auto_id"),
            }
            break

    latest_key = key_rows[-1] if key_rows else {}
    latest_uia = uia_rows[-1] if uia_rows else {}
    return {
        "latest_context_switch": latest_switch,
        "latest_key_context": latest_key.get("context"),
        "latest_key_surface": latest_key.get("surface"),
        "latest_key_type": latest_key.get("type"),
        "latest_key_buffer_len": latest_key.get("buffer_len"),
        "latest_uia_context": latest_uia.get("context"),
        "latest_uia_event": latest_uia.get("event"),
        "uia_rows_seen": len(uia_rows),
        "keystroke_rows_seen": len(key_rows),
    }


def _log_counts(root: Path) -> dict[str, int]:
    logs = root / "logs"
    names = [
        "prompt_journal",
        "chat_compositions",
        "edit_pairs",
        "training_pairs",
        "context_selection_history",
        "numeric_training_history",
        "tc_sim_results",
        "thought_composer_pauses",
        "thought_composer_rewards",
        "thought_composer_actions",
        "entropy_sheds",
        "intent_touches",
        "ai_responses",
        "unsaid_history",
        "unsaid_reconstructions",
        "uia_live",
        "os_keystrokes",
    ]
    counts: dict[str, int] = {}
    for name in names:
        path = logs / f"{name}.jsonl"
        if not path.exists():
            counts[name] = 0
            continue
        try:
            counts[name] = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            counts[name] = 0
    return counts


def _git_focus_files(git_status: list[str]) -> list[str]:
    files: list[str] = []
    for line in git_status:
        parts = line.strip().split(maxsplit=1)
        if not parts:
            continue
        candidate = parts[-1].strip()
        if candidate and candidate not in files:
            files.append(candidate)
    return files[:12]


def _deepseek_default_model() -> str:
    return os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro"


def _deepseek_api_key_present(root: Path) -> bool:
    if os.environ.get("DEEPSEEK_API_KEY"):
        return True
    env_path = Path(root) / ".env"
    if not env_path.exists():
        return False
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("DEEPSEEK_API_KEY=") and line.split("=", 1)[1].strip():
                return True
    except Exception:
        return False
    return False


def launch_deepseek_daemon(root: Path, dry_run: bool = False) -> dict[str, Any]:
    root = Path(root)
    script = root / "src" / "deepseek_daemon_seq001_v001.py"
    if not script.exists():
        return {"status": "missing", "target": str(script)}
    key_present = _deepseek_api_key_present(root)
    if not key_present and not dry_run:
        return {
            "status": "blocked",
            "reason": "DEEPSEEK_API_KEY missing; use --dry-run to smoke-test without API calls",
            "model": _deepseek_default_model(),
            "target": str(script),
        }
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    cmd = ["py", str(script), "--cycle-s", "12"]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.Popen(cmd, cwd=root, creationflags=flags)
    return {
        "status": "started",
        "pid": proc.pid,
        "dry_run": dry_run,
        "model": _deepseek_default_model(),
        "target": str(script),
    }


def enqueue_deepseek_prompt_job(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    context_pack: dict[str, Any] | None = None,
    deleted_words: list[Any] | None = None,
    source: str = "codex_prompt",
    priority: int = 5,
    mode: str = "coding_context",
) -> dict[str, Any] | None:
    """Queue a DeepSeek V4 coding/context job for the next daemon cycle."""
    prompt = str(prompt or "").strip()
    if not prompt:
        return None
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    context_selection = context_selection or (context_pack or {}).get("context_selection") or {}
    focus_files = (context_pack or {}).get("focus_files") or context_selection.get("files") or []
    signals = (context_pack or {}).get("signals") or {}
    parsed_deleted = _parse_deleted_words(deleted_words if deleted_words is not None else signals.get("deleted_words") or [], "")

    digest_src = json.dumps({
        "prompt": prompt,
        "source": source,
        "focus_files": focus_files[:8],
        "deleted_words": parsed_deleted[:12],
    }, sort_keys=True, ensure_ascii=False)
    job_id = "ds4-" + hashlib.sha256(digest_src.encode("utf-8")).hexdigest()[:16]

    recent = _load_jsonl_tail(logs / "deepseek_prompt_jobs.jsonl", max_lines=80)
    for row in recent:
        if row.get("job_id") == job_id:
            return {**row, "duplicate": True}

    job = {
        "ts": _utc_now(),
        "job_id": job_id,
        "status": "queued",
        "source": source,
        "mode": mode,
        "model": _deepseek_default_model(),
        "prompt": prompt,
        "deleted_words": parsed_deleted,
        "priority": priority,
        "focus_files": focus_files[:12],
        "context_confidence": context_selection.get("confidence", 0),
        "context_status": context_selection.get("status", "unknown"),
        "context_pack_path": "logs/dynamic_context_pack.json" if context_pack else "",
        "autonomous_write": os.environ.get("DEEPSEEK_AUTONOMOUS_PROMPT_WRITES", "").lower() in {"1", "true", "yes"},
    }
    _append_jsonl(logs / "deepseek_prompt_jobs.jsonl", job)
    (logs / "deepseek_prompt_latest.json").write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    return job


def _build_focus_files(
    context_selection: dict[str, Any],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    focus: list[dict[str, Any]] = []

    for item in context_selection.get("files") or []:
        name = str(item.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        focus.append({"name": name, "reason": "numeric_context", "score": item.get("score", 0)})

    for edit in state.get("recent_edits") or []:
        file_name = str(edit.get("file") or "").strip()
        if not file_name or file_name in seen:
            continue
        seen.add(file_name)
        focus.append({"name": file_name, "reason": "recent_edit", "why": edit.get("edit_why", "")})

    for file_name in _git_focus_files(state.get("git_status") or []):
        if file_name in seen:
            continue
        seen.add(file_name)
        focus.append({"name": file_name, "reason": "dirty_git"})

    entropy = state.get("entropy") or {}
    for item in entropy.get("top_entropy_modules") or []:
        name = str(item.get("module") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        focus.append({
            "name": name,
            "reason": "entropy_watch",
            "entropy": item.get("avg_entropy"),
            "samples": item.get("samples"),
        })

    return focus[:16]


def build_dynamic_context_pack(
    root: Path,
    prompt: str = "",
    deleted_words: list[Any] | None = None,
    surface: str = "codex",
    context_selection: dict[str, Any] | None = None,
    inject: bool = True,
) -> dict[str, Any]:
    """Write the compact context bundle that Codex/Copilot should read next."""
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    state = refresh_state(root, "dynamic context pack refreshed")
    latest_prompt = state.get("latest_prompt") or {}
    latest_composition = state.get("latest_composition") or {}
    prompt_text = (
        prompt.strip()
        or str(latest_prompt.get("msg") or "").strip()
        or str(latest_composition.get("final_text") or "").strip()
    )
    parsed_deleted = _parse_deleted_words(
        deleted_words if deleted_words is not None else latest_composition.get("deleted_words", []),
        "",
    )
    if context_selection is None:
        context_selection = (
            select_context(root, prompt_text, parsed_deleted)
            if prompt_text
            else state.get("latest_context_selection") or {}
        )

    intent_resolver = state.get("intent_resolver") or {}
    unresolved = []
    for item in (intent_resolver.get("intents") or [])[:5]:
        unresolved.append({
            "task": item.get("source_key") or item.get("ts"),
            "status": item.get("status"),
            "state": item.get("state"),
            "confidence": item.get("confidence"),
            "text": item.get("reconstructed") or item.get("msg"),
            "deleted_words": item.get("deleted_words", [])[:8],
        })

    signals = {
        "deletion_ratio": latest_composition.get("deletion_ratio", latest_prompt.get("signals", {}).get("deletion_ratio", 0)),
        "intent_deletion_ratio": latest_composition.get(
            "intent_deletion_ratio",
            latest_prompt.get("signals", {}).get("intent_deletion_ratio", 0),
        ),
        "hesitation_count": len(latest_composition.get("hesitation_windows", []))
        if isinstance(latest_composition.get("hesitation_windows"), list)
        else latest_prompt.get("signals", {}).get("hesitation_count", 0),
        "duration_ms": latest_composition.get("duration_ms", latest_prompt.get("signals", {}).get("duration_ms", 0)),
        "cognitive_state": latest_prompt.get("cognitive_state") or latest_composition.get("chat_state", {}).get("state"),
        "deleted_words": parsed_deleted,
    }

    capture_boundaries = {
        "composer": "pre-submit and blocking; pause and submit can inject before handoff",
        "copilot_vscode": "best with VS Code hook/composer; native chat submit needs a wrapper to guarantee pre-send injection",
        "codex_native_chat": "composition can be logged by external watcher, but this API path cannot block the already-sent Codex prompt",
        "screenshot_context": "not wired yet; UIA context switches are available now, screenshot/OCR can be layered next",
    }

    pack = {
        "ts": _utc_now(),
        "surface": surface,
        "prompt": prompt_text,
        "signals": signals,
        "context_selection": context_selection,
        "prompt_brain": _load_json(logs / "prompt_brain_latest.json") or {},
        "focus_files": _build_focus_files(context_selection or {}, state),
        "unresolved_intents": unresolved,
        "recent_training_pairs": state.get("recent_training_pairs") or [],
        "entropy": state.get("entropy") or {},
        "surface_activity": _surface_activity(root),
        "capture_boundaries": capture_boundaries,
        "log_counts": _log_counts(root),
        "paths": {
            "dynamic_context_pack_json": "logs/dynamic_context_pack.json",
            "dynamic_context_pack_md": "logs/dynamic_context_pack.md",
            "pre_prompt_state": "logs/pre_prompt_state.json",
            "codex_state": "logs/codex_state.json",
            "copilot_instructions": ".github/copilot-instructions.md",
        },
    }

    pack["deepseek_job"] = enqueue_deepseek_prompt_job(
        root,
        prompt_text,
        context_selection=context_selection,
        context_pack=pack,
        deleted_words=signals.get("deleted_words") or [],
        source=surface,
        priority=3,
    )
    pack["live_prompt_telemetry"] = _write_live_prompt_telemetry(root, pack)
    _write_copilot_live_query_blocks(root, pack, pack["live_prompt_telemetry"])
    (logs / "dynamic_context_pack.md").write_text(_render_dynamic_context_pack(pack) + "\n", encoding="utf-8")
    pack["injected"] = _inject_dynamic_context_pack(root, pack) if inject else False
    (logs / "dynamic_context_pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    return pack


def _render_dynamic_context_pack(pack: dict[str, Any], managed: bool = False) -> str:
    lines: list[str] = []
    if managed:
        lines.append("<!-- codex:dynamic-context-pack -->")
    lines.extend([
        "## Dynamic Context Pack",
        "",
        f"*Prepared {pack.get('ts', '')} for {pack.get('surface', 'unknown')}*",
        "",
        f"**PROMPT:** `{str(pack.get('prompt') or '')[:240]}`",
    ])

    signals = pack.get("signals") or {}
    lines.extend([
        f"**DELETION_RATIO:** `{signals.get('deletion_ratio', 0)}`",
        f"**INTENT_DELETION_RATIO:** `{signals.get('intent_deletion_ratio', 0)}`",
        f"**HESITATION_COUNT:** `{signals.get('hesitation_count', 0)}`",
        f"**COGNITIVE_STATE:** `{signals.get('cognitive_state') or 'unknown'}`",
        f"**DELETED_WORDS:** {', '.join(signals.get('deleted_words') or []) or 'none'}",
        "",
        "**FOCUS_FILES:**",
    ])
    focus_files = pack.get("focus_files") or []
    if focus_files:
        for item in focus_files[:10]:
            score = item.get("score")
            score_text = f" score={score}" if score is not None else ""
            reason = item.get("reason", "context")
            lines.append(f"- `{item.get('name', '?')}` via {reason}{score_text}")
    else:
        lines.append("- none")

    context = pack.get("context_selection") or {}
    lines.extend([
        "",
        f"**CONTEXT_CONFIDENCE:** `{context.get('confidence', 0)}`",
        f"**CONTEXT_STATUS:** `{context.get('status', 'unknown')}`",
        "",
        "**UNRESOLVED_INTENTS:**",
    ])
    unresolved = pack.get("unresolved_intents") or []
    if unresolved:
        for item in unresolved[:4]:
            lines.append(f"- `{item.get('status', '?')}` {str(item.get('text') or '')[:160]}")
    else:
        lines.append("- none")

    brain = pack.get("prompt_brain") or {}
    if brain:
        semantic = brain.get("semantic_profile") or {}
        lines.extend([
            "",
            "**PROMPT_BRAIN:**",
            f"- intent key: `{brain.get('intent_key') or 'none'}`",
            f"- semantic: `{', '.join(semantic.get('semantic_intents') or []) or 'none'}`",
            f"- profile hint: `{semantic.get('completion_hint') or 'none'}`",
            f"- prompt box open: `{(brain.get('prompt_box') or {}).get('open_count', 0)}`",
        ])

    activity = pack.get("surface_activity") or {}
    switch = activity.get("latest_context_switch") or {}
    lines.extend([
        "",
        "**SURFACE_ACTIVITY:**",
        f"- latest key surface: `{activity.get('latest_key_surface') or 'unknown'}`",
        f"- latest key context: `{activity.get('latest_key_context') or 'unknown'}`",
        f"- latest UIA context: `{activity.get('latest_uia_context') or 'unknown'}`",
    ])
    if switch:
        lines.append(f"- latest context switch: `{switch.get('from')}` -> `{switch.get('to')}`")

    entropy = pack.get("entropy") or {}
    if entropy.get("status") == "ok":
        lines.extend([
            "",
            f"**ENTROPY:** global H `{entropy.get('global_avg_entropy')}`, tracked `{entropy.get('tracked_modules')}`",
        ])

    deepseek = pack.get("deepseek_job") or {}
    if isinstance(deepseek, dict) and deepseek:
        lines.extend([
            "",
            "**DEEPSEEK_V4:**",
            f"- model: `{deepseek.get('model')}`",
            f"- job: `{deepseek.get('job_id')}` status `{deepseek.get('status')}`",
            f"- autonomous write: `{deepseek.get('autonomous_write', False)}`",
        ])

    boundaries = pack.get("capture_boundaries") or {}
    if boundaries:
        lines.extend(["", "**CAPTURE_BOUNDARY:**"])
        lines.append(f"- composer: {boundaries.get('composer')}")
        lines.append(f"- Codex native chat: {boundaries.get('codex_native_chat')}")
        lines.append(f"- screenshot context: {boundaries.get('screenshot_context')}")

    if managed:
        lines.append("<!-- /codex:dynamic-context-pack -->")
    return "\n".join(lines)


def run_pre_prompt_from_composition(
    root: Path,
    composition: dict[str, Any],
    run_sim: bool = False,
    sim_timeout_s: int = 15,
    inject: bool = True,
    trigger: str = "composition",
) -> dict[str, Any]:
    """Use an already-captured composition without duplicating the composition log."""
    root = Path(root)
    final_text = str(composition.get("final_text") or "").strip()
    deleted_words = _parse_deleted_words(
        list(composition.get("deleted_words") or []) + list(composition.get("intent_deleted_words") or []),
        str(composition.get("deleted_text") or ""),
    )
    rewrites = composition.get("rewrites") if isinstance(composition.get("rewrites"), list) else []
    hesitation_windows = composition.get("hesitation_windows") if isinstance(composition.get("hesitation_windows"), list) else []
    hesitation_count = len(hesitation_windows)
    duration_ms = int(composition.get("duration_ms") or 0)

    context = select_context(root, final_text, deleted_words, rewrites) if final_text else {}
    sim = _run_sim_buffer(root, final_text, timeout_s=sim_timeout_s) if (run_sim and final_text) else {
        "status": "skipped",
        "reason": "disabled",
    }
    handoff_ready = (not run_sim) or sim.get("status") == "ok"
    block_reason = "" if handoff_ready else f"thought-completer sim {sim.get('status', 'did_not_finish')}"
    state = {
        "ts": _utc_now(),
        "final_text": final_text,
        "trigger": trigger,
        "hesitation_count": hesitation_count,
        "duration_ms": duration_ms,
        "handoff_ready": handoff_ready,
        "block_reason": block_reason,
        "composition": composition,
        "context_selection": context,
        "sim": sim,
        "sim_latest": _latest_json(root / "logs" / "tc_sim_results.jsonl") or {},
        "tc_intent_reinjection": _load_json(root / "logs" / "tc_intent_reinjection.json") or {},
    }
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "pre_prompt_state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    (logs / "pre_prompt_state.md").write_text(_render_pre_prompt_block(state) + "\n", encoding="utf-8")
    state["injected"] = _inject_pre_prompt_state(root, state) if inject else False
    state["context_pack_path"] = "logs/dynamic_context_pack.json"
    build_dynamic_context_pack(root, final_text, deleted_words, surface=trigger, context_selection=context, inject=inject)
    (logs / "pre_prompt_state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    refresh_state(root, "pre-prompt from composition completed")
    return state


def run_pre_prompt_pipeline(
    root: Path,
    final_text: str,
    deleted_text: str = "",
    deleted_words: list[str] | None = None,
    rewrites: list[dict[str, Any]] | None = None,
    hesitation_count: int = 0,
    duration_ms: int = 0,
    run_sim: bool = True,
    sim_timeout_s: int = 45,
    inject: bool = True,
) -> dict[str, Any]:
    """Complete the pre-submit loop before a prompt is handed to a model.

    Ordered pipeline:
      1. Persist composition/deletions.
      2. Fire numeric context selection.
      3. Optionally run the thought-completer sim to completion.
      4. Write pre-prompt JSON/Markdown state.
      5. Inject a managed block into Copilot instructions.

    For true "before prompt reaches Copilot" semantics, a controlled submit path
    must call this function and wait for it before sending the prompt.
    """
    root = Path(root)
    composition = log_composition(
        root,
        final_text,
        deleted_text=deleted_text,
        deleted_words=deleted_words,
        rewrites=rewrites,
        hesitation_count=hesitation_count,
        duration_ms=duration_ms,
    )
    context = select_context(root, final_text, composition.get("deleted_words", []), rewrites or [])
    sim = _run_sim_buffer(root, final_text, timeout_s=sim_timeout_s) if run_sim else {
        "status": "skipped",
        "reason": "disabled",
    }
    handoff_ready = (not run_sim) or sim.get("status") == "ok"
    block_reason = "" if handoff_ready else f"thought-completer sim {sim.get('status', 'did_not_finish')}"
    sim_latest = _latest_json(root / "logs" / "tc_sim_results.jsonl") or {}
    reinjection = _load_json(root / "logs" / "tc_intent_reinjection.json") or {}

    state = {
        "ts": _utc_now(),
        "final_text": final_text,
        "hesitation_count": hesitation_count,
        "duration_ms": duration_ms,
        "handoff_ready": handoff_ready,
        "block_reason": block_reason,
        "composition": composition,
        "context_selection": context,
        "sim": sim,
        "sim_latest": sim_latest,
        "tc_intent_reinjection": reinjection,
    }
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "pre_prompt_state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (logs / "pre_prompt_state.md").write_text(_render_pre_prompt_block(state) + "\n", encoding="utf-8")
    state["injected"] = _inject_pre_prompt_state(root, state) if inject else False
    state["context_pack_path"] = "logs/dynamic_context_pack.json"
    try:
        build_dynamic_context_pack(
            root,
            final_text,
            composition.get("deleted_words", []),
            surface="pre_prompt",
            context_selection=context,
            inject=inject,
        )
    except Exception as exc:
        state["context_pack_error"] = str(exc)
    (logs / "pre_prompt_state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    refresh_state(root, "pre-prompt pipeline completed")
    return state


def select_context(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    rewrites: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    agent = _load_context_select_agent()
    if agent is None:
        result = {
            "ts": _utc_now(),
            "buffer": prompt[:200],
            "intent_keys": prompt[:300],
            "files": [],
            "stale_blocks": [],
            "confidence": 0.0,
            "status": "missing_context_select_agent",
        }
    else:
        try:
            result = agent.run_assembly(root, prompt, deleted_words or [], rewrites or [])
            result["status"] = "ok"
        except Exception as exc:
            result = {
                "ts": _utc_now(),
                "buffer": prompt[:200],
                "intent_keys": prompt[:300],
                "files": [],
                "stale_blocks": [],
                "confidence": 0.0,
                "status": "error",
                "error": str(exc),
            }

    if not result.get("files"):
        numeric_files = predict_numeric_files(root, " ".join([prompt, *(deleted_words or [])]))
        if numeric_files:
            result["files"] = numeric_files
            result["confidence"] = numeric_files[0]["score"]
            result["fallback"] = "intent_numeric_direct"
            (root / "logs" / "context_selection.json").write_text(
                json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    _append_jsonl(root / "logs" / "context_selection_history.jsonl", result)
    return result


def refresh_state(root: Path, note: str = "") -> dict[str, Any]:
    """Write browseable Codex loop state for humans and automation."""
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    prompts = _load_jsonl_tail(logs / "prompt_journal.jsonl", max_lines=5)
    responses = _load_jsonl_tail(logs / "ai_responses.jsonl", max_lines=5)
    edits = _load_jsonl_tail(logs / "edit_pairs.jsonl", max_lines=12)
    pairs = _load_jsonl_tail(logs / "training_pairs.jsonl", max_lines=5)
    compositions = _load_jsonl_tail(logs / "chat_compositions.jsonl", max_lines=5)
    context_history = _load_jsonl_tail(logs / "context_selection_history.jsonl", max_lines=5)
    numeric_training = _load_jsonl_tail(logs / "numeric_training_history.jsonl", max_lines=5)
    intent_resolver = _load_json(root / "logs" / "codex_intent_resolver.json") or {}
    entropy = _refresh_entropy(root)

    state = {
        "ts": _utc_now(),
        "status": "active",
        "note": note,
        "latest_prompt": prompts[-1] if prompts else None,
        "latest_response": responses[-1] if responses else None,
        "recent_edits": edits,
        "recent_training_pairs": pairs,
        "latest_composition": compositions[-1] if compositions else None,
        "latest_context_selection": context_history[-1] if context_history else None,
        "latest_numeric_training": numeric_training[-1] if numeric_training else None,
        "intent_resolver": intent_resolver,
        "git_status": _git_status(root),
        "entropy": entropy,
        "paths": {
            "human_state": "logs/codex_state.md",
            "machine_state": "logs/codex_state.json",
            "entropy_block": "logs/codex_entropy_block.md",
            "prompt_journal": "logs/prompt_journal.jsonl",
            "edit_pairs": "logs/edit_pairs.jsonl",
            "training_pairs": "logs/training_pairs.jsonl",
            "chat_compositions": "logs/chat_compositions.jsonl",
            "context_selection": "logs/context_selection.json",
            "context_selection_history": "logs/context_selection_history.jsonl",
            "numeric_training_history": "logs/numeric_training_history.jsonl",
            "pre_prompt_state": "logs/pre_prompt_state.json",
            "dynamic_context_pack": "logs/dynamic_context_pack.json",
            "deepseek_prompt_jobs": "logs/deepseek_prompt_jobs.jsonl",
            "deepseek_prompt_results": "logs/deepseek_prompt_results.jsonl",
            "intent_resolver": "logs/codex_intent_resolver.json",
        },
    }

    (logs / "codex_state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    (logs / "codex_state.md").write_text(_render_state_markdown(state), encoding="utf-8")
    return state


def _render_state_markdown(state: dict[str, Any]) -> str:
    prompt = state.get("latest_prompt") or {}
    response = state.get("latest_response") or {}
    edits = state.get("recent_edits") or []
    pairs = state.get("recent_training_pairs") or []
    entropy = state.get("entropy") or {}
    composition = state.get("latest_composition") or {}
    context_selection = state.get("latest_context_selection") or {}
    numeric_training = state.get("latest_numeric_training") or {}
    intent_resolver = state.get("intent_resolver") or {}
    git_status = state.get("git_status") or []

    lines = [
        "# Codex Loop State",
        "",
        f"- updated: `{state.get('ts', '')}`",
        f"- status: `{state.get('status', 'unknown')}`",
    ]
    if state.get("note"):
        lines.append(f"- note: {state['note']}")

    lines += [
        "",
        "## Latest Prompt",
        "",
        prompt.get("msg", "_none yet_") if isinstance(prompt, dict) else "_none yet_",
        "",
        "## Latest Response",
        "",
        (response.get("response", "")[:700] or "_none yet_") if isinstance(response, dict) else "_none yet_",
        "",
        "## Recent Edits",
        "",
    ]
    if edits:
        for edit in reversed(edits[-8:]):
            lines.append(
                f"- `{edit.get('file', 'unknown')}` | {edit.get('edit_why', 'codex edit')} | "
                f"session `{edit.get('session_n', '?')}`"
            )
    else:
        lines.append("_none yet_")

    lines += ["", "## Numeric Training", ""]
    if isinstance(numeric_training, dict) and numeric_training:
        lines.append(f"- status: `{numeric_training.get('status', 'unknown')}`")
        lines.append(f"- vocab: `{numeric_training.get('vocab_size', 0)}`")
        lines.append(f"- files tracked: `{numeric_training.get('files_tracked', 0)}`")
        lines.append(f"- touches: `{numeric_training.get('total_touches', 0)}`")
        for file_name in numeric_training.get("files", [])[:8]:
            lines.append(f"- `{file_name}`")
    else:
        lines.append("_none yet_")

    lines += ["", "## Context Selection", ""]
    if isinstance(context_selection, dict) and context_selection:
        lines.append(f"- status: `{context_selection.get('status', 'unknown')}`")
        lines.append(f"- confidence: `{context_selection.get('confidence', 0)}`")
        lines.append(f"- intent keys: `{context_selection.get('intent_keys', '')[:160]}`")
        files = context_selection.get("files") or []
        if files:
            for file_ref in files[:8]:
                lines.append(f"- `{file_ref.get('name', '?')}` score={file_ref.get('score', 0)}")
        else:
            lines.append("- files: `none`")
    else:
        lines.append("_none yet_")

    lines += ["", "## Deletions", ""]
    if isinstance(composition, dict) and composition:
        deleted_words = _parse_deleted_words(
            composition.get("deleted_words") or [],
            str(composition.get("deleted_text") or ""),
        )
        lines.append(f"- deletion ratio: `{composition.get('deletion_ratio', 0)}`")
        lines.append(f"- deleted words: `{', '.join(deleted_words[:12]) or 'none'}`")
        if composition.get("unsaid_reconstruction"):
            lines.append(f"- unsaid: {composition.get('unsaid_reconstruction')}")
    else:
        lines.append("_none yet_")

    lines += ["", "## Intent Resolver", ""]
    if isinstance(intent_resolver, dict) and intent_resolver:
        lines.append(f"- unresolved: `{intent_resolver.get('unresolved_count', 0)}`")
        lines.append(f"- abandoned: `{intent_resolver.get('abandoned', 0)}`")
        lines.append(f"- partial: `{intent_resolver.get('partial', 0)}`")
        lines.append(f"- cold: `{intent_resolver.get('cold', 0)}`")
        for item in (intent_resolver.get("intents") or [])[:5]:
            lines.append(f"- `{item.get('status', '?')}` {item.get('reconstructed', '')[:120]}")
    else:
        lines.append("_not pushed yet_")

    lines += ["", "## Training Pairs", ""]
    if pairs:
        for pair in reversed(pairs[-5:]):
            user = pair.get("user_intent", {}).get("raw_prompt", "")[:90]
            work = pair.get("completion", {}).get("work_note", "")[:90]
            lines.append(f"- {user} -> {work}")
    else:
        lines.append("_none yet_")

    lines += ["", "## Entropy", ""]
    if entropy.get("status") == "ok":
        lines.append(f"- global H: `{entropy.get('global_avg_entropy')}`")
        lines.append(f"- tracked modules: `{entropy.get('tracked_modules')}`")
        for item in entropy.get("top_entropy_modules", []):
            lines.append(f"- `{item.get('module')}` H={item.get('avg_entropy')} samples={item.get('samples')}")
        lines.append("")
        lines.append("See `logs/codex_entropy_block.md` for the prompt block.")
    else:
        lines.append(f"- entropy status: `{entropy.get('status')}`")
        if entropy.get("error"):
            lines.append(f"- reason: `{entropy.get('error')}`")

    lines += ["", "## Git Status", ""]
    if git_status:
        lines.extend(f"- `{line}`" for line in git_status)
    else:
        lines.append("_clean or unavailable_")

    lines += [
        "",
        "## Browseable Files",
        "",
        "- `logs/codex_state.json`",
        "- `logs/codex_state.md`",
        "- `logs/codex_entropy_block.md`",
        "- `logs/prompt_journal.jsonl`",
        "- `logs/edit_pairs.jsonl`",
        "- `logs/training_pairs.jsonl`",
        "- `logs/chat_compositions.jsonl`",
        "- `logs/context_selection.json`",
        "- `logs/context_selection_history.jsonl`",
        "- `logs/numeric_training_history.jsonl`",
        "- `logs/pre_prompt_state.json`",
        "- `logs/pre_prompt_state.md`",
        "- `logs/dynamic_context_pack.json`",
        "- `logs/dynamic_context_pack.md`",
        "- `logs/deepseek_prompt_jobs.jsonl`",
        "- `logs/deepseek_prompt_results.jsonl`",
        "- `logs/codex_intent_resolver.json`",
    ]
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _next_session_n(root: Path) -> int:
    rows = _load_jsonl_tail(root / "logs" / "prompt_journal.jsonl", max_lines=1)
    if not rows:
        return 1
    try:
        return int(rows[-1].get("session_n", 0)) + 1
    except (TypeError, ValueError):
        return 1


def _classify_intent(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in ("fix", "bug", "error", "broken", "wrong", "fail")):
        return "debugging"
    if any(word in text for word in ("add", "create", "build", "implement", "wire")):
        return "building"
    if any(word in text for word in ("refactor", "rename", "move", "split", "cleanup")):
        return "restructuring"
    if any(word in text for word in ("test", "verify", "check", "run")):
        return "testing"
    if any(word in text for word in ("why", "how", "what", "explain", "analyze", "inspect")):
        return "exploring"
    return "unknown"


def log_prompt(
    root: Path,
    prompt: str,
    ts: str | None = None,
    session_n: int | None = None,
    deleted_words: list[str] | None = None,
    deleted_text: str = "",
    deletion_ratio: float | None = None,
    hesitation_count: int = 0,
    duration_ms: int = 0,
    total_keystrokes: int = 0,
    rewrites: list[dict[str, Any]] | None = None,
    source: str = "codex_explicit",
) -> dict[str, Any]:
    root = Path(root)
    session_n = session_n or _next_session_n(root)
    prompt = prompt.strip()
    parsed_deleted_words = _parse_deleted_words(deleted_words, deleted_text)
    if deletion_ratio is None:
        deleted_chars = len(deleted_text)
        denominator = max(len(prompt) + deleted_chars, 1)
        deletion_ratio = round(deleted_chars / denominator, 3) if deleted_chars else 0
    deletion_ratio = max(0.0, min(1.0, float(deletion_ratio)))
    total_keystrokes = total_keystrokes or len(prompt) + len(deleted_text)
    entry = {
        "ts": ts or _utc_now(),
        "session_n": session_n,
        "session_id": f"codex-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "msg": prompt,
        "intent": _classify_intent(prompt),
        "cognitive_state": _state_from_deletions(deletion_ratio, hesitation_count),
        "signals": {
            "wpm": 0,
            "chars_per_sec": 0,
            "deletion_ratio": deletion_ratio,
            "intent_deletion_ratio": deletion_ratio,
            "hesitation_count": hesitation_count,
            "rewrite_count": len(rewrites or []),
            "typo_corrections": 0,
            "intentional_deletions": len(parsed_deleted_words),
            "total_keystrokes": total_keystrokes,
            "duration_ms": duration_ms,
        },
        "deleted_words": parsed_deleted_words,
        "rewrites": rewrites or [],
        "module_refs": [],
        "source": source,
    }
    try:
        from src.tc_semantic_profile_seq001_v001 import log_semantic_profile_event
        entry["semantic_profile"] = log_semantic_profile_event(
            root,
            prompt,
            source=source,
            deleted_words=parsed_deleted_words,
        )
    except Exception as exc:
        entry["semantic_profile_error"] = str(exc)
    _append_jsonl(root / "logs" / "prompt_journal.jsonl", entry)
    context = select_context(root, prompt, parsed_deleted_words, rewrites or [])
    try:
        enqueue_deepseek_prompt_job(
            root,
            prompt,
            context_selection=context,
            deleted_words=parsed_deleted_words,
            source=source,
            priority=4,
        )
    except Exception:
        pass
    refresh_state(root, "logged prompt")
    return entry


def log_composition(
    root: Path,
    final_text: str,
    deleted_text: str = "",
    deleted_words: list[str] | None = None,
    rewrites: list[dict[str, Any]] | None = None,
    hesitation_count: int = 0,
    duration_ms: int = 0,
) -> dict[str, Any]:
    root = Path(root)
    parsed_deleted_words = _parse_deleted_words(deleted_words, deleted_text)
    deletion_ratio = round(len(deleted_text) / max(len(final_text) + len(deleted_text), 1), 3) if deleted_text else 0
    entry = {
        "ts": _utc_now(),
        "final_text": final_text,
        "deleted_text": deleted_text[:1000],
        "deleted_words": parsed_deleted_words,
        "intent_deleted_words": parsed_deleted_words,
        "deletion_ratio": deletion_ratio,
        "intent_deletion_ratio": deletion_ratio,
        "hesitation_windows": [{} for _ in range(max(0, hesitation_count))],
        "rewrites": rewrites or [],
        "total_keystrokes": len(final_text) + len(deleted_text),
        "duration_ms": duration_ms,
        "source": "codex_composition",
        "unsaid_reconstruction": _build_unsaid_reconstruction(final_text, parsed_deleted_words),
    }
    _append_jsonl(root / "logs" / "chat_compositions.jsonl", entry)
    _write_unsaid(root, entry)
    log_prompt(
        root,
        final_text,
        deleted_words=parsed_deleted_words,
        deleted_text=deleted_text,
        deletion_ratio=deletion_ratio,
        hesitation_count=hesitation_count,
        duration_ms=duration_ms,
        total_keystrokes=entry["total_keystrokes"],
        rewrites=rewrites,
        source="codex_composition",
    )
    refresh_state(root, "logged composition with deletions")
    return entry


def _build_unsaid_reconstruction(final_text: str, deleted_words: list[str]) -> str:
    if not deleted_words:
        return ""
    return f"{final_text[:120]}... (also considered: {' '.join(deleted_words[:8])})"


def _write_unsaid(root: Path, composition: dict[str, Any]) -> None:
    deleted_words = _parse_deleted_words(
        composition.get("deleted_words") if isinstance(composition.get("deleted_words"), list) else [],
        str(composition.get("deleted_text") or ""),
    )
    if not deleted_words:
        return
    reconstructed = composition.get("unsaid_reconstruction", "")
    latest = {
        "ts": composition.get("ts"),
        "fragment": " ".join(deleted_words[:12]),
        "completed_intent": reconstructed,
        "deleted_words": deleted_words,
        "context": "codex",
        "source": "codex_composition",
    }
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "unsaid_latest.json").write_text(json.dumps(latest, indent=2, ensure_ascii=False), encoding="utf-8")
    _append_jsonl(logs / "unsaid_history.jsonl", latest)
    _append_jsonl(
        logs / "unsaid_reconstructions.jsonl",
        {
            "ts": composition.get("ts"),
            "deleted_words": deleted_words,
            "reconstructed_intent": reconstructed,
            "source": "codex_composition",
        },
    )


def log_response(
    root: Path,
    prompt: str,
    response: str,
    ts: str | None = None,
    response_id: str | None = None,
) -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": ts or _utc_now(),
        "prompt": prompt.strip(),
        "response": response.strip(),
        "response_id": response_id or f"codex:{datetime.now(timezone.utc).timestamp():.0f}",
        "capture_surface": "codex",
    }
    _append_jsonl(root / "logs" / "ai_responses.jsonl", entry)
    refresh_state(root, "logged response")
    return entry


def _git_changed_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def log_edit(
    root: Path,
    file: str | None = None,
    why: str = "codex edit",
    prompt: str | None = None,
    ts: str | None = None,
    session_n: int | None = None,
) -> list[dict[str, Any]]:
    root = Path(root)
    journal_tail = _load_jsonl_tail(root / "logs" / "prompt_journal.jsonl", max_lines=1)
    latest_prompt = journal_tail[-1] if journal_tail else {}
    session_n = session_n or int(latest_prompt.get("session_n", 0) or 0)
    prompt = prompt if prompt is not None else str(latest_prompt.get("msg", ""))
    files = [file] if file else _git_changed_files(root)
    if not files:
        files = ["unknown"]

    now = ts or _utc_now()
    records = []
    for changed in files:
        entry = {
            "ts": now,
            "prompt_ts": latest_prompt.get("ts", now),
            "prompt_msg": prompt[:200],
            "file": changed,
            "edit_ts": now,
            "edit_why": why,
            "edit_hash": "codex",
            "latency_ms": 0,
            "state": latest_prompt.get("cognitive_state", "unknown"),
            "session_n": session_n,
            "source": "codex_explicit",
        }
        _append_jsonl(root / "logs" / "edit_pairs.jsonl", entry)
        records.append(entry)
    train_numeric_surface(root, prompt, files)
    refresh_state(root, f"logged {len(records)} edit(s)")
    return records


def capture_pair(root: Path) -> dict[str, Any] | None:
    root = Path(root)
    repo = _repo_root()
    src_dir = repo / "src"
    candidates = sorted(src_dir.glob("*s027*.py"), key=lambda item: item.name)
    for candidate in candidates:
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if "def capture_training_pair" not in text or "def _load_jsonl_tail" not in text:
            continue
        spec = importlib.util.spec_from_file_location("codex_training_pairs", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pair = module.capture_training_pair(root)
        refresh_state(root, "captured training pair")
        return pair
    raise ImportError(f"No complete training pair module found under {src_dir}")


def record_entropy_shed(root: Path, module: str, confidence: float, note: str = "") -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": _utc_now(),
        "module": module,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "note": note,
        "source": "codex_explicit",
    }
    _append_jsonl(root / "logs" / "entropy_sheds.jsonl", entry)
    refresh_state(root, f"recorded entropy shed for {module}")
    return entry


def push_intent_resolver(root: Path, prompt_limit: int = 100) -> dict[str, Any]:
    root = Path(root)
    reconstructor = _load_intent_reconstructor()
    if reconstructor is None:
        result = {"status": "missing", "error": "intent_reconstructor_seq001_v001.py not found"}
    else:
        try:
            result = reconstructor.refresh_intent_backlog(root, prompt_limit)
            result["status"] = "ok"
        except Exception as exc:
            result = {"status": "error", "error": str(exc)}
    out = root / "logs" / "codex_intent_resolver.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    refresh_state(root, "pushed to intent resolver")
    return result


def _text_from_event(event: dict[str, Any]) -> str:
    for key in ("content", "text", "message", "prompt", "response"):
        value = event.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or ""))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part)
    return ""


def import_jsonl(root: Path, source: Path, capture: bool = True) -> dict[str, int]:
    root = Path(root)
    counts = {"prompts": 0, "responses": 0, "edits": 0, "pairs": 0}
    last_prompt = ""

    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        event_type = str(event.get("type") or event.get("event") or "").lower()
        role = str(event.get("role") or "").lower()
        text = _text_from_event(event)
        ts = event.get("ts") or event.get("timestamp") or event.get("time")

        if role == "user" or event_type in {"user", "user_message", "prompt"}:
            if text.strip():
                deleted_text = str(event.get("deleted_text") or "")
                deleted_words = event.get("deleted_words") if isinstance(event.get("deleted_words"), list) else []
                entry = log_prompt(root, text, ts=ts, deleted_words=deleted_words, deleted_text=deleted_text)
                last_prompt = entry["msg"]
                counts["prompts"] += 1
        elif event_type in {"composition", "chat_composition"}:
            if text.strip():
                deleted_text = str(event.get("deleted_text") or "")
                deleted_words = event.get("deleted_words") if isinstance(event.get("deleted_words"), list) else []
                log_composition(root, text, deleted_text=deleted_text, deleted_words=deleted_words)
                last_prompt = text
                counts["prompts"] += 1
        elif role == "assistant" or event_type in {"assistant", "assistant_message", "response"}:
            if text.strip():
                prompt = str(event.get("prompt") or last_prompt)
                log_response(root, prompt, text, ts=ts)
                counts["responses"] += 1
        elif event_type in {"edit", "file_change", "file_edit", "tool_edit"}:
            changed = event.get("file") or event.get("path") or event.get("target")
            why = str(event.get("why") or event.get("summary") or event.get("message") or "codex edit")
            records = log_edit(root, file=str(changed) if changed else None, why=why, prompt=last_prompt, ts=ts)
            counts["edits"] += len(records)
            if capture:
                pair = capture_pair(root)
                if pair:
                    counts["pairs"] += 1
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bridge explicit Codex events into telemetry training logs.")
    parser.add_argument("--root", default=".", help="Repo root to write logs into.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prompt = sub.add_parser("log-prompt")
    p_prompt.add_argument("--prompt", required=True)
    p_prompt.add_argument("--deleted-text", default="")
    p_prompt.add_argument("--deleted-word", action="append", default=[])
    p_prompt.add_argument("--deletion-ratio", type=float)
    p_prompt.add_argument("--hesitation-count", type=int, default=0)
    p_prompt.add_argument("--duration-ms", type=int, default=0)

    p_comp = sub.add_parser("log-composition")
    p_comp.add_argument("--final-text", required=True)
    p_comp.add_argument("--deleted-text", default="")
    p_comp.add_argument("--deleted-word", action="append", default=[])
    p_comp.add_argument("--hesitation-count", type=int, default=0)
    p_comp.add_argument("--duration-ms", type=int, default=0)

    p_pre = sub.add_parser("pre-prompt")
    p_pre.add_argument("--final-text", required=True)
    p_pre.add_argument("--deleted-text", default="")
    p_pre.add_argument("--deleted-word", action="append", default=[])
    p_pre.add_argument("--hesitation-count", type=int, default=0)
    p_pre.add_argument("--duration-ms", type=int, default=0)
    p_pre.add_argument("--no-sim", action="store_true")
    p_pre.add_argument("--sim-timeout-s", type=int, default=45)
    p_pre.add_argument("--no-inject", action="store_true")

    p_select = sub.add_parser("select-context")
    p_select.add_argument("--prompt", required=True)
    p_select.add_argument("--deleted-word", action="append", default=[])

    p_pack = sub.add_parser("context-pack")
    p_pack.add_argument("--prompt", default="")
    p_pack.add_argument("--deleted-word", action="append", default=[])
    p_pack.add_argument("--surface", default="codex")
    p_pack.add_argument("--no-inject", action="store_true")

    p_train = sub.add_parser("train-numeric")
    p_train.add_argument("--prompt", required=True)
    p_train.add_argument("--file", action="append", required=True)

    p_predict = sub.add_parser("predict-numeric")
    p_predict.add_argument("--prompt", required=True)
    p_predict.add_argument("--top-n", type=int, default=6)

    p_response = sub.add_parser("log-response")
    p_response.add_argument("--prompt", required=True)
    p_response.add_argument("--response", required=True)

    p_edit = sub.add_parser("log-edit")
    p_edit.add_argument("--file")
    p_edit.add_argument("--why", default="codex edit")
    p_edit.add_argument("--prompt")

    sub.add_parser("capture-pair")
    sub.add_parser("state")

    p_shed = sub.add_parser("shed")
    p_shed.add_argument("--module", required=True)
    p_shed.add_argument("--confidence", type=float, required=True)
    p_shed.add_argument("--note", default="")

    p_launch = sub.add_parser("launch-observatory")
    p_launch.add_argument("--thought-completer", action="store_true")

    p_deepseek = sub.add_parser("launch-deepseek")
    p_deepseek.add_argument("--dry-run", action="store_true")

    p_intent = sub.add_parser("push-intent-resolver")
    p_intent.add_argument("--prompt-limit", type=int, default=100)

    p_import = sub.add_parser("import-jsonl")
    p_import.add_argument("source")
    p_import.add_argument("--no-capture", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "log-prompt":
        result: Any = log_prompt(
            root,
            args.prompt,
            deleted_words=args.deleted_word,
            deleted_text=args.deleted_text,
            deletion_ratio=args.deletion_ratio,
            hesitation_count=args.hesitation_count,
            duration_ms=args.duration_ms,
        )
    elif args.command == "log-composition":
        result = log_composition(
            root,
            args.final_text,
            deleted_text=args.deleted_text,
            deleted_words=args.deleted_word,
            hesitation_count=args.hesitation_count,
            duration_ms=args.duration_ms,
        )
    elif args.command == "pre-prompt":
        result = run_pre_prompt_pipeline(
            root,
            args.final_text,
            deleted_text=args.deleted_text,
            deleted_words=args.deleted_word,
            hesitation_count=args.hesitation_count,
            duration_ms=args.duration_ms,
            run_sim=not args.no_sim,
            sim_timeout_s=args.sim_timeout_s,
            inject=not args.no_inject,
        )
    elif args.command == "select-context":
        result = select_context(root, args.prompt, args.deleted_word)
    elif args.command == "context-pack":
        result = build_dynamic_context_pack(
            root,
            prompt=args.prompt,
            deleted_words=args.deleted_word,
            surface=args.surface,
            inject=not args.no_inject,
        )
    elif args.command == "train-numeric":
        result = train_numeric_surface(root, args.prompt, args.file)
    elif args.command == "predict-numeric":
        result = predict_numeric_files(root, args.prompt, args.top_n)
    elif args.command == "log-response":
        result = log_response(root, args.prompt, args.response)
    elif args.command == "log-edit":
        result = log_edit(root, file=args.file, why=args.why, prompt=args.prompt)
    elif args.command == "capture-pair":
        result = capture_pair(root)
    elif args.command == "state":
        result = refresh_state(root, "manual refresh")
    elif args.command == "shed":
        result = record_entropy_shed(root, args.module, args.confidence, args.note)
    elif args.command == "launch-observatory":
        if args.thought_completer:
            target = root / "src" / "thought_completer.py"
            cmd = ["py", str(target), "--observatory", "--no-gemini"]
        else:
            matches = sorted((root / "src").glob("*tc_observatory*.py"))
            target = matches[-1] if matches else root / "src" / "tc_observatory_seq001_v001.py"
            cmd = ["py", str(target)]
        proc = subprocess.Popen(cmd, cwd=root)
        result = {"status": "started", "pid": proc.pid, "target": str(target)}
    elif args.command == "launch-deepseek":
        result = launch_deepseek_daemon(root, dry_run=args.dry_run)
    elif args.command == "push-intent-resolver":
        result = push_intent_resolver(root, args.prompt_limit)
    elif args.command == "import-jsonl":
        result = import_jsonl(root, Path(args.source), capture=not args.no_capture)
    else:
        raise AssertionError(args.command)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
