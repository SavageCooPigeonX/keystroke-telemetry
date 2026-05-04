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
import sys
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


def _state_from_deletions(deletion_ratio: float, hesitation_count: int = 0, prompt: str = "") -> str:
    if deletion_ratio > 0.4 or hesitation_count > 5:
        return "frustrated"
    if deletion_ratio > 0.2 or hesitation_count > 2:
        return "hesitant"
    if deletion_ratio > 0:
        return "neutral"
    inferred = _state_from_prompt_text(prompt)
    if inferred:
        return inferred
    return "unknown"


def _state_from_prompt_text(prompt: str) -> str:
    text = str(prompt or "").lower()
    if not text:
        return ""
    frustrated_terms = (
        "broken", "doesnt work", "doesn't work", "still not", "wtf", "fuck",
        "shit", "stale", "missing", "dead", "wrong", "bug", "failed", "fail",
        "doesnt", "doesn't", "cannot", "can't", "no data", "not rendering",
        "doesnt render", "doesn't render", "how come", "why can",
    )
    hesitant_terms = (
        "hmm", "umm", "maybe", "lost", "confused", "not sure", "how do",
        "what would", "why is", "assess", "audit", "diagnose",
        "should", "or am i missing", "do you think",
    )
    focused_terms = (
        "fix", "run", "wire", "make", "implement", "push", "test", "verify",
        "submit", "send", "email", "refactor", "decompose",
        "proceed", "execute", "do that", "write", "render", "compile",
        "close", "optimize", "monitor", "investigation", "intent", "query",
        "graph", "grapgh", "profile", "model favorability", "mfs",
    )
    if any(term in text for term in frustrated_terms):
        return "frustrated"
    if any(term in text for term in hesitant_terms):
        return "hesitant"
    if any(term in text for term in focused_terms):
        return "focused"
    return ""


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


def _ensure_repo_on_path(root: Path) -> None:
    root_s = str(Path(root).resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)


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
    file_sim = state.get("file_sim") or {}
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
        f"**FILE_SIM_STATUS:** `{file_sim.get('status', 'not_run')}`",
        f"**FILE_SIM_TARGET_STATE:** `{file_sim.get('target_state', 'none')}`",
    ])
    proposals = file_sim.get("proposals") or []
    if proposals:
        lines.append("**FILE_SIM_SOURCE_REWRITES:**")
        for proposal in proposals[:5]:
            lines.append(
                f"- `{proposal.get('path')}` interlink={proposal.get('interlink_score')} "
                f"decision={proposal.get('decision')}"
            )
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
    probe_packet = (context_pack or {}).get("copilot_probe_push_cycle") or {}
    probe_orchestration = probe_packet.get("file_sim_orchestration") if isinstance(probe_packet, dict) else {}
    probe_handoff = probe_packet.get("deepseek_compiler_handoff") if isinstance(probe_packet, dict) else {}
    probe_focus = (probe_orchestration or {}).get("waking_files") if isinstance(probe_orchestration, dict) else []
    focus_files = probe_focus or (context_pack or {}).get("focus_files") or context_selection.get("files") or []
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
        "context_pack_path": (
            (probe_handoff or {}).get("context_pack_path")
            if isinstance(probe_handoff, dict)
            else ""
        ) or ("logs/dynamic_context_pack.json" if context_pack else ""),
        "dynamic_context_pack_path": "logs/dynamic_context_pack.json" if context_pack else "",
        "probe_cycle_id": probe_packet.get("cycle_id") if isinstance(probe_packet, dict) else "",
        "operator_prompt": (context_pack or {}).get("prompt") or prompt,
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
        "file_sim": _load_json(logs / "batch_rewrite_sim_latest.json") or {},
        "intent_loop": _load_json(logs / "intent_loop_latest.json") or {},
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

    try:
        _ensure_repo_on_path(root)
        from src.file_self_knowledge_seq001_v001 import build_file_self_knowledge
        pack["file_self_knowledge"] = build_file_self_knowledge(
            root,
            files=pack.get("focus_files") or [],
            prompt=prompt_text,
            limit=8,
            write=True,
        )
    except Exception as exc:
        pack["file_self_knowledge"] = {"status": "error", "error": str(exc)}

    try:
        _ensure_repo_on_path(root)
        from src.copilot_probe_push_cycle_seq001_v001 import build_copilot_probe_push_cycle
        pack["copilot_probe_push_cycle"] = build_copilot_probe_push_cycle(
            root,
            prompt_text,
            deleted_words=signals.get("deleted_words") or [],
            context_pack=pack,
            context_selection=context_selection,
            focus_files=pack.get("focus_files") or [],
            source=surface,
            write=True,
        )
    except Exception as exc:
        pack["copilot_probe_push_cycle"] = {"status": "error", "error": str(exc)}

    deepseek_prompt = prompt_text
    probe_packet = pack.get("copilot_probe_push_cycle") if isinstance(pack.get("copilot_probe_push_cycle"), dict) else {}
    probe_handoff = (probe_packet or {}).get("deepseek_compiler_handoff") if isinstance(probe_packet, dict) else {}
    if isinstance(probe_handoff, dict) and probe_handoff.get("compiler_prompt"):
        deepseek_prompt = str(probe_handoff.get("compiler_prompt") or prompt_text)

    pack["deepseek_job"] = enqueue_deepseek_prompt_job(
        root,
        deepseek_prompt,
        context_selection=context_selection,
        context_pack=pack,
        deleted_words=signals.get("deleted_words") or [],
        source=f"{surface}:probe_push_cycle" if probe_packet and not probe_packet.get("status") else surface,
        priority=0 if probe_packet and not probe_packet.get("status") else 3,
        mode="probe_push_cycle" if probe_packet and not probe_packet.get("status") else "coding_context",
    )
    pack["live_prompt_telemetry"] = _write_live_prompt_telemetry(root, pack)
    _write_copilot_live_query_blocks(root, pack, pack["live_prompt_telemetry"])
    try:
        _ensure_repo_on_path(root)
        from src.operator_response_policy_seq001_v001 import build_operator_response_policy
        pack["operator_response_policy"] = build_operator_response_policy(
            root,
            prompt_text,
            surface=surface,
            context_pack=pack,
            inject=inject,
            write=True,
        )
    except Exception as exc:
        pack["operator_response_policy"] = {"status": "error", "error": str(exc)}
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

    probe = pack.get("copilot_probe_push_cycle") or {}
    if isinstance(probe, dict) and not probe.get("status"):
        probe_read = (probe.get("operator_probe") or {}).get("read") or ""
        handoff = probe.get("deepseek_compiler_handoff") or {}
        waking_names = [
            str(row.get("name"))
            for row in ((probe.get("file_sim_orchestration") or {}).get("waking_files") or [])[:6]
            if isinstance(row, dict) and row.get("name")
        ]
        lines.extend([
            "",
            "**COPILOT_PROBE_PUSH_CYCLE:**",
            f"- cycle: `{probe.get('cycle_id')}`",
            f"- read: {str(probe_read)[:320]}",
            f"- deepseek context: `{handoff.get('context_pack_path') or 'logs/copilot_probe_push_cycle_latest.json'}`",
            f"- waking files: `{', '.join(waking_names) or 'none'}`",
        ])

    self_knowledge = pack.get("file_self_knowledge") or {}
    if isinstance(self_knowledge, dict) and self_knowledge.get("packets"):
        lines.extend([
            "",
            "**FILE_SELF_KNOWLEDGE:**",
            f"- read: {str(self_knowledge.get('operator_read') or '')[:260]}",
        ])
        for packet in (self_knowledge.get("packets") or [])[:5]:
            scope = packet.get("mutation_scope") or {}
            owns = ", ".join(packet.get("owns") or [])[:120] or "unknown"
            lines.append(
                f"- `{packet.get('file')}` owns `{owns}` readiness `{scope.get('readiness')}`"
            )
            validates = packet.get("validates_with") or []
            if validates:
                lines.append(f"  - validates: `{validates[0]}`")
            quote = packet.get("file_quote")
            if quote:
                lines.append(f"  - says: {quote}")

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

    policy = pack.get("operator_response_policy") or {}
    if isinstance(policy, dict) and policy:
        lines.extend([
            "",
            "**OPERATOR_RESPONSE_POLICY:**",
            f"- active arm: `{policy.get('active_arm', 'unknown')}`",
            f"- operator read: {str(policy.get('operator_read') or '')[:220]}",
            f"- required sections: `{', '.join(policy.get('required_sections') or [])}`",
            f"- next mutation: {str(policy.get('next_mutation') or '')[:220]}",
        ])
        for move in (policy.get("intent_moves") or [])[:5]:
            lines.append(f"- intent move: `{move.get('intent_key', 'none')}`")
        for item in (policy.get("probe_files") or [])[:6]:
            lines.append(f"- probe file: `{item.get('file')}` via {item.get('reason', 'policy')}")

    file_sim = pack.get("file_sim") or {}
    if file_sim:
        proposals = file_sim.get("proposals") or []
        lines.extend([
            "",
            "**FILE_SIM:**",
            f"- status: `{file_sim.get('status', 'unknown')}`",
            f"- target state: `{file_sim.get('target_state', 'unknown')}`",
            f"- trigger: `{file_sim.get('trigger', 'unknown')}`",
        ])
        for proposal in proposals[:5]:
            lines.append(
                f"- `{proposal.get('path')}` interlink={proposal.get('interlink_score')} "
                f"decision={proposal.get('decision')}"
            )

    intent_loop = pack.get("intent_loop") or {}
    if intent_loop:
        lines.extend([
            "",
            "**INTENT_LOOP:**",
            f"- loop: `{intent_loop.get('loop_id', 'none')}` status `{intent_loop.get('status', 'unknown')}`",
            f"- intent: `{intent_loop.get('intent_key', 'none')}`",
            f"- human: `{intent_loop.get('human_position', 'on_loop')}` approval_required `{intent_loop.get('approval_required', True)}`",
            f"- observed edits: `{len(intent_loop.get('observed_edits') or [])}` responses: `{len(intent_loop.get('observed_responses') or [])}`",
        ])
        for action in (intent_loop.get("next_actions") or [])[:3]:
            lines.append(f"- next: {action}")

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
    return "\n".join(line.rstrip() for line in lines)


def _fire_file_sim(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    trigger: str = "pre_prompt",
    force: bool = False,
) -> dict[str, Any]:
    root = Path(root)
    try:
        _ensure_repo_on_path(root)
        from src.batch_rewrite_sim_seq001_v001 import (
            load_file_sim_config,
            should_fire_file_sim,
            simulate_batch_rewrites,
        )
        config = load_file_sim_config(root, write_default=True)
        if not force and not should_fire_file_sim(config, trigger, prompt):
            return {
                "status": "skipped",
                "reason": "disabled_or_trigger_filtered",
                "trigger": trigger,
                "file_sim_config": config,
            }
        if force and not config.get("enabled", True):
            return {
                "status": "skipped",
                "reason": "disabled",
                "trigger": trigger,
                "file_sim_config": config,
            }
        return simulate_batch_rewrites(
            root,
            prompt,
            limit=int(config.get("max_proposals") or 6),
            write=True,
            config=config,
            trigger=trigger,
            context_selection=context_selection,
        )
    except Exception as exc:
        return {"status": "error", "trigger": trigger, "error": str(exc)}


def _record_intent_loop(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    file_sim: dict[str, Any] | None = None,
    prompt_brain: dict[str, Any] | None = None,
    source: str = "prompt",
    deleted_words: list[str] | None = None,
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import record_intent_loop
        return record_intent_loop(
            root,
            prompt,
            context_selection=context_selection,
            file_sim=file_sim,
            prompt_brain=prompt_brain,
            source=source,
            deleted_words=deleted_words,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "source": source}


def _emit_codex_prompt_email(
    root: Path,
    prompt_entry: dict[str, Any],
    loop: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.file_email_plugin_seq001_v001 import emit_codex_prompt_email
        return emit_codex_prompt_email(root, prompt_entry, loop=loop)
    except Exception as exc:
        return {"status": "error", "phase": "codex_prompt", "error": str(exc)}


def _bind_intent_loop_response(root: Path, response_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import bind_response_to_latest_loop
        return bind_response_to_latest_loop(root, response_entry)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _bind_intent_loop_edit(root: Path, edit_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import bind_edit_to_latest_loop
        return bind_edit_to_latest_loop(root, edit_entry)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def close_intent_loop(
    root: Path,
    loop_id: str | None = None,
    status: str = "verified",
    note: str = "",
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import close_intent_loop as _close
        return _close(root, loop_id=loop_id, status=status, note=note)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def get_intent_loop_status(root: Path) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import intent_loop_summary
        return intent_loop_summary(root)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _parse_iso_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _latest_log_ts(root: Path, rel_path: str) -> tuple[datetime | None, dict[str, Any]]:
    path = root / rel_path
    if rel_path.endswith(".jsonl"):
        row = _latest_json(path) or {}
        return _parse_iso_ts(row.get("ts")), row
    data = _load_json(path) or {}
    return _parse_iso_ts(data.get("ts")), data


def audit_stale_dates(root: Path, max_lag_minutes: int = 30) -> dict[str, Any]:
    root = Path(root)
    logs = root / "logs"
    now = datetime.now(timezone.utc)
    surfaces = {
        "prompt_journal": "logs/prompt_journal.jsonl",
        "chat_compositions": "logs/chat_compositions.jsonl",
        "pre_prompt_state": "logs/pre_prompt_state.json",
        "dynamic_context_pack": "logs/dynamic_context_pack.json",
        "batch_rewrite_sim": "logs/batch_rewrite_sim_latest.json",
        "intent_loop": "logs/intent_loop_latest.json",
        "file_email_outbox": "logs/file_email_outbox.jsonl",
        "resend_payload": "logs/resend_payload_latest.json",
        "deepseek_prompt": "logs/deepseek_prompt_latest.json",
    }
    rows = {}
    latest_prompt_ts = None
    for name, rel in surfaces.items():
        ts, data = _latest_log_ts(root, rel)
        if name == "prompt_journal":
            latest_prompt_ts = ts
        rows[name] = {
            "path": rel,
            "ts": ts.isoformat() if ts else "",
            "age_minutes": round((now - ts).total_seconds() / 60, 2) if ts else None,
            "status": data.get("status") if isinstance(data, dict) else None,
            "trigger": data.get("trigger") if isinstance(data, dict) else None,
        }
    baseline = latest_prompt_ts or now
    for row in rows.values():
        ts = _parse_iso_ts(row.get("ts"))
        row["lag_from_prompt_minutes"] = round((baseline - ts).total_seconds() / 60, 2) if ts else None
        row["stale"] = bool(ts and (baseline - ts).total_seconds() > max_lag_minutes * 60)

    latest_comp = _latest_json(logs / "chat_compositions.jsonl") or {}
    hidden_words = _parse_deleted_words(
        list(latest_comp.get("deleted_words") or []) + list(latest_comp.get("intent_deleted_words") or []),
        str(latest_comp.get("deleted_text") or ""),
    )
    file_sim_config = _load_json(logs / "file_sim_config.json") or {}
    pre_prompt = _load_json(logs / "pre_prompt_state.json") or {}
    trigger = str(pre_prompt.get("trigger") or "")
    fire_on = file_sim_config.get("fire_on") if isinstance(file_sim_config.get("fire_on"), list) else []
    result = {
        "schema": "stale_date_audit/v1",
        "ts": now.isoformat(),
        "max_lag_minutes": max_lag_minutes,
        "latest_prompt_ts": baseline.isoformat(),
        "hidden_words_latest": hidden_words,
        "trigger_audit": {
            "latest_pre_prompt_trigger": trigger,
            "file_sim_fire_on": fire_on,
            "trigger_allowed": (not trigger) or trigger in fire_on,
        },
        "surfaces": rows,
        "stale": [name for name, row in rows.items() if row.get("stale")],
    }
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "stale_date_audit_latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Stale Date Audit",
        "",
        f"- latest_prompt_ts: `{result['latest_prompt_ts']}`",
        f"- max_lag_minutes: `{max_lag_minutes}`",
        f"- hidden_words_latest: `{', '.join(hidden_words) or 'none'}`",
        f"- trigger_allowed: `{result['trigger_audit']['trigger_allowed']}`",
        "",
        "## Surfaces",
        "",
    ]
    for name, row in rows.items():
        lines.append(
            f"- `{name}` ts `{row.get('ts') or 'missing'}` lag `{row.get('lag_from_prompt_minutes')}` stale `{row.get('stale')}`"
        )
    (logs / "stale_date_audit_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


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
    if final_text:
        try:
            _ensure_repo_on_path(root)
            from src.tc_prompt_brain_seq001_v001 import assemble_prompt_brain
            state["prompt_brain"] = assemble_prompt_brain(
                root,
                final_text,
                deleted_words=deleted_words,
                rewrites=rewrites,
                source=trigger,
                trigger="composition_submit",
                emit_prompt_box=False,
                inject=inject,
                context_selection=context,
            )
        except Exception as exc:
            state["prompt_brain_error"] = str(exc)
    state["file_sim"] = _fire_file_sim(root, final_text, context_selection=context, trigger=trigger, force=True) if final_text else {
        "status": "skipped",
        "reason": "empty_prompt",
    }
    if final_text:
        state["intent_loop"] = _record_intent_loop(
            root,
            final_text,
            context_selection=context,
            file_sim=state.get("file_sim"),
            prompt_brain=state.get("prompt_brain"),
            source=trigger,
            deleted_words=deleted_words,
        )
        state["codex_prompt_email"] = _emit_codex_prompt_email(
            root,
            {
                "ts": state.get("ts"),
                "session_n": None,
                "msg": final_text,
                "intent": "codex_prompt",
                "source": trigger,
                "deleted_words": deleted_words,
                "signals": {
                    "hesitation_count": hesitation_count,
                    "duration_ms": duration_ms,
                    "intentional_deletions": len(deleted_words),
                },
                "context_selection": context,
                "file_sim": state.get("file_sim"),
            },
            loop=state.get("intent_loop"),
        )
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
    emit_prompt_email: bool = True,
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
        fire_file_sim=False,
        emit_prompt_email=False,
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
    if final_text:
        try:
            _ensure_repo_on_path(root)
            from src.tc_prompt_brain_seq001_v001 import assemble_prompt_brain
            state["prompt_brain"] = assemble_prompt_brain(
                root,
                final_text,
                deleted_words=composition.get("deleted_words", []),
                rewrites=rewrites or [],
                source="pre_prompt",
                trigger="composition_submit",
                emit_prompt_box=False,
                inject=inject,
                context_selection=context,
            )
        except Exception as exc:
            state["prompt_brain_error"] = str(exc)
    state["file_sim"] = _fire_file_sim(root, final_text, context_selection=context, trigger="pre_prompt", force=True) if final_text else {
        "status": "skipped",
        "reason": "empty_prompt",
    }
    if final_text:
        state["intent_loop"] = _record_intent_loop(
            root,
            final_text,
            context_selection=context,
            file_sim=state.get("file_sim"),
            prompt_brain=state.get("prompt_brain"),
            source="pre_prompt",
            deleted_words=composition.get("deleted_words", []),
        )
        if emit_prompt_email:
            state["codex_prompt_email"] = _emit_codex_prompt_email(
                root,
                {
                    "ts": state.get("ts"),
                    "session_n": None,
                    "msg": final_text,
                    "intent": "codex_prompt",
                    "source": "pre_prompt",
                    "deleted_words": composition.get("deleted_words", []),
                    "signals": {
                        "hesitation_count": hesitation_count,
                        "duration_ms": duration_ms,
                        "intentional_deletions": len(composition.get("deleted_words", [])),
                    },
                    "context_selection": context,
                    "file_sim": state.get("file_sim"),
                },
                loop=state.get("intent_loop"),
            )
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
    if any(word in text for word in (
        "orchestrator", "10q", "consensus", "approval", "approve", "guard",
        "copilot", "deepseek", "file sim", "file_sim", "autonomous",
    )):
        return "orchestration"
    if any(word in text for word in ("email", "emails", "resend", "outbox", "alert", "alerts")):
        return "telemetry"
    if any(word in text for word in ("monitor", "watch", "observe", "observatory")):
        return "monitoring"
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
    fire_file_sim: bool = True,
    emit_prompt_email: bool = True,
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
        "cognitive_state": _state_from_deletions(deletion_ratio, hesitation_count, prompt),
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
        _ensure_repo_on_path(root)
        from src.tc_semantic_profile_seq001_v001 import log_semantic_profile_event
        entry["semantic_profile"] = log_semantic_profile_event(
            root,
            prompt,
            source=source,
            deleted_words=parsed_deleted_words,
        )
    except Exception as exc:
        entry["semantic_profile_error"] = str(exc)
    context = select_context(root, prompt, parsed_deleted_words, rewrites or [])
    entry["context_selection"] = context
    entry["file_sim"] = (
        _fire_file_sim(root, prompt, context_selection=context, trigger="log_prompt", force=True)
        if fire_file_sim
        else {"status": "skipped", "reason": "pre_prompt_will_fire", "trigger": "log_prompt"}
    )
    if prompt and fire_file_sim:
        entry["intent_loop"] = _record_intent_loop(
            root,
            prompt,
            context_selection=context,
            file_sim=entry.get("file_sim"),
            prompt_brain=_load_json(root / "logs" / "prompt_brain_latest.json") or {},
            source=source,
            deleted_words=parsed_deleted_words,
        )
    if prompt and emit_prompt_email:
        entry["codex_prompt_email"] = _emit_codex_prompt_email(root, entry, loop=entry.get("intent_loop"))
    _append_jsonl(root / "logs" / "prompt_journal.jsonl", entry)
    try:
        _ensure_repo_on_path(root)
        from src.ai_fingerprint_operator_seq001_v001 import build_operator_fingerprint
        build_operator_fingerprint(root)
    except Exception:
        pass
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
    fire_file_sim: bool = True,
    emit_prompt_email: bool = True,
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
        fire_file_sim=fire_file_sim,
        emit_prompt_email=emit_prompt_email,
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
    style_arm: str | None = None,
    hook_ids: list[str] | None = None,
    intent_nodes: list[str] | None = None,
    context_window_files: list[str] | None = None,
    reward_features: dict[str, Any] | None = None,
    feedback_text: str = "",
) -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": ts or _utc_now(),
        "prompt": prompt.strip(),
        "response": response.strip(),
        "response_id": response_id or f"codex:{datetime.now(timezone.utc).timestamp():.0f}",
        "capture_surface": "codex",
    }
    try:
        _ensure_repo_on_path(root)
        from src.operator_response_policy_seq001_v001 import (
            record_response_reward,
            response_log_defaults,
        )
        defaults = response_log_defaults(root, prompt, response)
        resolved_style_arm = style_arm or defaults.get("style_arm") or "probe_council"
        resolved_intent_nodes = intent_nodes if intent_nodes is not None else defaults.get("intent_nodes", [])
        resolved_hook_ids = hook_ids if hook_ids is not None else defaults.get("hook_ids", [])
        resolved_files = context_window_files if context_window_files is not None else defaults.get("context_window_files", [])
        resolved_features = reward_features if reward_features is not None else defaults.get("reward_features", {})
        entry["response_policy"] = {
            "style_arm": resolved_style_arm,
            "intent_nodes": resolved_intent_nodes,
            "hook_ids": resolved_hook_ids,
            "context_window_files": resolved_files,
            "reward_features": resolved_features,
        }
        reward_event = record_response_reward(
            root,
            {
                "ts": entry["ts"],
                "response_id": entry["response_id"],
                "prompt": entry["prompt"],
                "response": entry["response"],
                "style_arm": resolved_style_arm,
                "intent_nodes": resolved_intent_nodes,
                "hook_ids": resolved_hook_ids,
                "context_window_files": resolved_files,
                "reward_features": resolved_features,
                "feedback_text": feedback_text,
            },
            write=True,
        )
        entry["reward_event"] = {
            "score": reward_event.get("score"),
            "weighted_score": reward_event.get("weighted_score"),
            "dimension_scores": reward_event.get("dimension_scores", {}),
            "style_model": reward_event.get("style_model", {}),
        }
    except Exception as exc:
        entry["response_policy_error"] = str(exc)
    entry["intent_loop_binding"] = _bind_intent_loop_response(root, entry)
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
        try:
            _ensure_repo_on_path(root)
            from src.file_email_plugin_seq001_v001 import emit_touch_email
            entry["file_email"] = emit_touch_email(root, changed, why=why, prompt=prompt)
        except Exception as exc:
            entry["file_email_error"] = str(exc)
        entry["intent_loop_binding"] = _bind_intent_loop_edit(root, entry)
        _append_jsonl(root / "logs" / "edit_pairs.jsonl", entry)
        records.append(entry)
    train_numeric_surface(root, prompt, files)
    refresh_state(root, f"logged {len(records)} edit(s)")
    return records


def capture_pair(root: Path) -> dict[str, Any] | None:
    root = Path(root)
    repo = _repo_root()
    src_dir = repo / "src"
    search_roots = [
        src_dir,
        repo / "build" / "pigeon_legacy" / "src",
    ]
    candidates: list[Path] = []
    for search_root in search_roots:
        if search_root.exists():
            candidates.extend(sorted(search_root.rglob("*.py"), key=lambda item: str(item)))
    for candidate in candidates:
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if "def capture_training_pair" not in text or "def _load_jsonl_tail" not in text:
            continue
        module_key = re.sub(r"[^0-9A-Za-z_]+", "_", str(candidate.relative_to(repo)))
        spec = importlib.util.spec_from_file_location(f"codex_training_pairs_{module_key}", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pair = module.capture_training_pair(root)
        refresh_state(root, "captured training pair")
        return pair
    roots = ", ".join(str(item) for item in search_roots if item.exists())
    raise ImportError(f"No complete training pair module found under {roots}")


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

    p_self = sub.add_parser("file-self-knowledge")
    p_self.add_argument("--prompt", default="")
    p_self.add_argument("--file", action="append", default=[])
    p_self.add_argument("--limit", type=int, default=8)
    p_self.add_argument("--no-write", action="store_true")

    p_train = sub.add_parser("train-numeric")
    p_train.add_argument("--prompt", required=True)
    p_train.add_argument("--file", action="append", required=True)

    p_predict = sub.add_parser("predict-numeric")
    p_predict.add_argument("--prompt", required=True)
    p_predict.add_argument("--top-n", type=int, default=6)

    p_response = sub.add_parser("log-response")
    p_response.add_argument("--prompt", required=True)
    p_response.add_argument("--response", required=True)
    p_response.add_argument("--style-arm")
    p_response.add_argument("--hook-id", action="append", default=[])
    p_response.add_argument("--intent-node", action="append", default=[])
    p_response.add_argument("--context-window-file", action="append", default=[])
    p_response.add_argument("--feedback", default="")

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

    sub.add_parser("intent-loop-status")

    p_close_loop = sub.add_parser("close-intent-loop")
    p_close_loop.add_argument("--loop-id")
    p_close_loop.add_argument("--status", default="verified")
    p_close_loop.add_argument("--note", default="")

    p_stale = sub.add_parser("stale-date-audit")
    p_stale.add_argument("--max-lag-minutes", type=int, default=30)

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
    elif args.command == "file-self-knowledge":
        _ensure_repo_on_path(root)
        from src.file_self_knowledge_seq001_v001 import build_file_self_knowledge
        result = build_file_self_knowledge(
            root,
            files=args.file,
            prompt=args.prompt,
            limit=args.limit,
            write=not args.no_write,
        )
    elif args.command == "train-numeric":
        result = train_numeric_surface(root, args.prompt, args.file)
    elif args.command == "predict-numeric":
        result = predict_numeric_files(root, args.prompt, args.top_n)
    elif args.command == "log-response":
        result = log_response(
            root,
            args.prompt,
            args.response,
            style_arm=args.style_arm,
            hook_ids=args.hook_id,
            intent_nodes=args.intent_node,
            context_window_files=args.context_window_file,
            feedback_text=args.feedback,
        )
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
    elif args.command == "intent-loop-status":
        result = get_intent_loop_status(root)
    elif args.command == "close-intent-loop":
        result = close_intent_loop(root, loop_id=args.loop_id, status=args.status, note=args.note)
    elif args.command == "stale-date-audit":
        result = audit_stale_dates(root, max_lag_minutes=args.max_lag_minutes)
    elif args.command == "import-jsonl":
        result = import_jsonl(root, Path(args.source), capture=not args.no_capture)
    else:
        raise AssertionError(args.command)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((output + "\n").encode("utf-8", errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
