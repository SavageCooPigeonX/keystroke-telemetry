"""File-first unsaid thread digest for low-friction thought completion.

This replaces "popup must catch me" with a pasteable/readable context file:
recent deleted thoughts, pause sims, prompt-brain context, and open hooks are
compiled into a small set of threads Copilot/Codex can close.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "unsaid_thread_digest/v1"


def build_unsaid_thread_digest(
    root: Path,
    prompt: str = "",
    limit: int = 5,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    sources = _load_sources(root)
    threads = _rank_threads(root, prompt, sources, limit)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "mode": "file_first_low_friction",
        "prompt": str(prompt or ""),
        "sources": {
            "unsaid_history": len(sources["unsaid_history"]),
            "composer_pauses": len(sources["composer_pauses"]),
            "tc_sims": len(sources["tc_sims"]),
            "prompt_brain": len(sources["prompt_brain"]),
            "chat_compositions": len(sources["chat_compositions"]),
            "prompt_journal": len(sources["prompt_journal"]),
        },
        "threads": threads,
        "paste_block": _render_paste_block(threads),
        "architecture_read": _architecture_read(),
        "paths": {
            "latest": "logs/unsaid_thread_digest_latest.json",
            "markdown": "logs/unsaid_thread_digest.md",
            "paste": "logs/copilot_unsaid_context.md",
            "history": "logs/unsaid_thread_digest.jsonl",
        },
    }
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        _write_json(logs / "unsaid_thread_digest_latest.json", result)
        _append_jsonl(logs / "unsaid_thread_digest.jsonl", result)
        (logs / "unsaid_thread_digest.md").write_text(render_unsaid_thread_digest(result), encoding="utf-8")
        (logs / "copilot_unsaid_context.md").write_text(result["paste_block"] + "\n", encoding="utf-8")
    return result


def render_unsaid_thread_digest(result: dict[str, Any]) -> str:
    lines = [
        "# Unsaid Thread Digest",
        "",
        "File-first thought completion: no popup required. Read this, paste the useful threads, close them with Copilot/Codex.",
        "",
        "```text",
        f"mode: {result.get('mode')}",
        f"prompt: {result.get('prompt') or 'none'}",
        f"threads: {len(result.get('threads') or [])}",
        "```",
        "",
        "## Paste Block",
        "",
        result.get("paste_block") or "No threads yet.",
        "",
        "## Threads",
        "",
    ]
    for thread in result.get("threads") or []:
        lines.extend([
            f"### {thread.get('id')} - {thread.get('title')}",
            "",
            f"- source: `{thread.get('source')}`",
            f"- score: `{thread.get('score')}`",
            f"- intent key: `{thread.get('intent_key') or 'none'}`",
            f"- files: `{', '.join(thread.get('files') or []) or 'none'}`",
            f"- sim completion: {thread.get('sim_completion') or 'none'}",
            f"- close with: {thread.get('close_with')}",
            "",
            f"> You were going to say: {thread.get('you_were_going_to_say')}",
            "",
        ])
    lines.extend([
        "## Architecture Read",
        "",
        result.get("architecture_read") or "",
        "",
    ])
    return "\n".join(lines)


def _load_sources(root: Path) -> dict[str, list[dict[str, Any]]]:
    logs = root / "logs"
    return {
        "unsaid_history": _jsonl(logs / "unsaid_history.jsonl", 80),
        "composer_pauses": _jsonl(logs / "thought_composer_pauses.jsonl", 80),
        "tc_sims": _jsonl(logs / "tc_sim_results.jsonl", 120),
        "prompt_brain": _jsonl(logs / "prompt_brain_history.jsonl", 80),
        "chat_compositions": _jsonl(logs / "chat_compositions.jsonl", 120),
        "prompt_journal": _jsonl(logs / "prompt_journal.jsonl", 80),
    }


def _rank_threads(
    root: Path,
    prompt: str,
    sources: dict[str, list[dict[str, Any]]],
    limit: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    candidates.extend(_threads_from_unsaid(sources["unsaid_history"]))
    candidates.extend(_threads_from_composer(sources["composer_pauses"]))
    candidates.extend(_threads_from_sims(sources["tc_sims"]))
    candidates.extend(_threads_from_compositions(sources["chat_compositions"]))
    candidates.extend(_threads_from_prompt_brain(sources["prompt_brain"]))
    candidates.extend(_threads_from_journal(sources["prompt_journal"]))
    prompt_terms = set(_tokens(prompt))
    for item in candidates:
        inferred = _infer_files_for_thread(root, item)
        item["files"] = _dedupe([*(item.get("files") or []), *inferred])[:8]
        item["score"] = round(_score_thread(item, prompt_terms), 4)
        item["id"] = "unsaid-" + _digest("|".join([
            item.get("source", ""),
            item.get("you_were_going_to_say", ""),
            item.get("intent_key", ""),
        ]))[:10]
        item["title"] = _title(item)
        item["close_with"] = _close_with(item)
    deduped = _dedupe_threads(candidates)
    deduped.sort(key=lambda item: (item["score"], item.get("ts", "")), reverse=True)
    return deduped[: max(1, int(limit or 5))]


def _threads_from_unsaid(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows[-40:]:
        text = row.get("completed_intent") or row.get("fragment") or " ".join(row.get("unsaid_threads") or [])
        if not text:
            continue
        out.append({
            "source": "unsaid_history",
            "ts": row.get("ts", ""),
            "you_were_going_to_say": _clean(text),
            "deleted_words": row.get("deleted_words") or [],
            "intent_key": row.get("intent_key", ""),
            "files": _files_from_text(text),
            "sim_completion": "",
        })
    return out


def _threads_from_composer(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows[-40:]:
        pre = row.get("pre_prompt") if isinstance(row.get("pre_prompt"), dict) else {}
        comp = pre.get("composition") if isinstance(pre.get("composition"), dict) else {}
        text = pre.get("final_text") or comp.get("final_text") or ""
        sim_latest = pre.get("sim_latest") if isinstance(pre.get("sim_latest"), dict) else {}
        prompt_brain = pre.get("prompt_brain") if isinstance(pre.get("prompt_brain"), dict) else {}
        if not text:
            continue
        out.append({
            "source": "composer_pause",
            "ts": row.get("ts", ""),
            "you_were_going_to_say": _clean(text),
            "deleted_words": comp.get("deleted_words") or [],
            "intent_key": _intent_key(prompt_brain.get("intent_key") or pre.get("intent_key")),
            "files": _context_files(prompt_brain, sim_latest),
            "sim_completion": _clean(sim_latest.get("completion") or sim_latest.get("action_path") or ""),
            "hesitation_count": comp.get("hesitation_count", 0),
        })
    return out


def _threads_from_sims(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows[-60:]:
        intent = row.get("intent") or row.get("buffer") or row.get("prompt") or ""
        completion = row.get("completion") or row.get("action_path") or ""
        if not intent and not completion:
            continue
        out.append({
            "source": "tc_sim",
            "ts": row.get("ts", ""),
            "you_were_going_to_say": _clean(intent or completion),
            "deleted_words": row.get("deleted_words") or [],
            "intent_key": row.get("intent_key", ""),
            "files": _dedupe([*row.get("files", []), *_files_from_text(completion)]),
            "sim_completion": _clean(completion),
            "sim_score": row.get("score", 0),
        })
    return out


def _threads_from_compositions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows[-60:]:
        deleted = []
        for item in row.get("intent_deleted_words") or row.get("deleted_words") or []:
            deleted.append(str(item.get("word") if isinstance(item, dict) else item))
        text = row.get("final_text") or row.get("text") or row.get("prompt") or ""
        if not text and not deleted:
            continue
        phrase = text or "deleted: " + ", ".join(deleted[:8])
        out.append({
            "source": "chat_composition",
            "ts": row.get("ts", ""),
            "you_were_going_to_say": _clean(phrase),
            "deleted_words": deleted,
            "intent_key": row.get("intent_key", ""),
            "files": _files_from_text(phrase),
            "sim_completion": "",
        })
    return out


def _threads_from_prompt_brain(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows[-40:]:
        prompt = row.get("prompt") or ""
        if not prompt:
            continue
        out.append({
            "source": "prompt_brain",
            "ts": row.get("ts", ""),
            "you_were_going_to_say": _clean(prompt),
            "deleted_words": row.get("deleted_words") or [],
            "intent_key": _intent_key(row.get("intent_key")),
            "files": _context_files(row, {}),
            "sim_completion": _clean((row.get("semantic_profile") or {}).get("completion_hint") or ""),
        })
    return out


def _threads_from_journal(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows[-40:]:
        text = row.get("msg") or row.get("prompt") or row.get("text") or ""
        if not text:
            continue
        out.append({
            "source": "prompt_journal",
            "ts": row.get("ts", ""),
            "you_were_going_to_say": _clean(text),
            "deleted_words": [],
            "intent_key": row.get("intent_key", ""),
            "files": row.get("module_refs") or _files_from_text(text),
            "sim_completion": "",
        })
    return out


def _score_thread(item: dict[str, Any], prompt_terms: set[str]) -> float:
    text_terms = set(_tokens(" ".join([
        item.get("you_were_going_to_say", ""),
        item.get("sim_completion", ""),
        " ".join(item.get("deleted_words") or []),
    ])))
    score = 0.2
    score += min(len(text_terms & prompt_terms), 8) * 0.35 if prompt_terms else 0
    score += 1.2 if item.get("source") in {"composer_pause", "unsaid_history"} else 0
    score += 0.7 if item.get("sim_completion") else 0
    score += 0.5 if item.get("intent_key") else 0
    score += min(len(item.get("files") or []), 5) * 0.18
    score += min(len(item.get("deleted_words") or []), 5) * 0.12
    score += float(item.get("sim_score") or 0) * 0.4
    return score


def _render_paste_block(threads: list[dict[str, Any]]) -> str:
    lines = [
        "## Unsaid Threads To Close",
        "",
        "Use these as prompt-history injection. Close or reject them explicitly.",
        "",
    ]
    for i, thread in enumerate(threads, 1):
        files = ", ".join(thread.get("files") or []) or "none selected"
        deleted = ", ".join(thread.get("deleted_words") or []) or "none"
        lines.extend([
            f"{i}. {thread.get('you_were_going_to_say')}",
            f"   - source: `{thread.get('source')}` score `{thread.get('score')}`",
            f"   - files: `{files}`",
            f"   - deleted/unsaid: `{deleted}`",
            f"   - sim said: {thread.get('sim_completion') or 'no sim yet'}",
            f"   - close with Copilot/Codex: {thread.get('close_with')}",
            "",
        ])
    return "\n".join(lines).rstrip()


def _close_with(item: dict[str, Any]) -> str:
    files = item.get("files") or []
    if files:
        return f"load `{files[0]}` plus its test, then ask for the smallest validating patch or rejection"
    if item.get("sim_completion"):
        return "turn the sim completion into an approved bounded task, then run validation"
    if item.get("deleted_words"):
        return "decide whether the deleted phrase is real intent or discard it with a reason"
    return "classify this as intent, note, or noise before injecting it again"


def _architecture_read() -> str:
    return "\n".join([
        "- Thought Completer owns pause/deletion reconstruction and prompt-history injection.",
        "- File Sim owns code-context diagnosis: which files wake, what they think, what validation blocks overwrite.",
        "- Prompt Brain is the deterministic context bundle: intent key, semantic profile, manifest, numeric files, prompt box.",
        "- Engagement Hooks are not the UI; they are the bait layer that brings back unresolved or deleted intent.",
        "- Low-friction path: write files first (`copilot_unsaid_context.md`, `pre_prompt_state.md`, `file_self_sim_learning_email.md`), popup only displays or copies.",
    ])


def _context_files(prompt_brain: dict[str, Any], sim_latest: dict[str, Any]) -> list[str]:
    out = []
    context = prompt_brain.get("context_selection") if isinstance(prompt_brain.get("context_selection"), dict) else {}
    for item in context.get("files") or []:
        if isinstance(item, dict):
            out.append(str(item.get("path") or item.get("name") or ""))
        else:
            out.append(str(item))
    out.extend(str(item) for item in sim_latest.get("files") or [])
    return _dedupe([item for item in out if item])[:8]


def _infer_files_for_thread(root: Path, item: dict[str, Any]) -> list[str]:
    haystack = " ".join([
        item.get("you_were_going_to_say", ""),
        item.get("sim_completion", ""),
        item.get("intent_key", ""),
        " ".join(item.get("deleted_words") or []),
    ]).lower()
    hints = [
        (
            {"hook", "hooks", "engagement", "unsaid", "reconstruct", "reconstructed", "deleted", "deletion"},
            [
                "src/engagement_hooks_seq001_v001.py",
                "src/unsaid_accumulator_seq001_v001.py",
                "src/prompt_recon_seq016_v001.py",
                "client/composition_recon_seq001_v001.py",
                "client/os_hook.py",
            ],
        ),
        (
            {"thought", "completer", "popup", "pause", "hesitation", "composer", "completion"},
            [
                "src/thought_completer.py",
                "src/tc_prompt_composer_seq001_v001.py",
                "src/tc_popup_seq001_v004*.py",
                "src/tc_buffer_watcher_seq001_v001.py",
            ],
        ),
        (
            {"prompt", "brain", "context", "copilot", "codex", "inject", "injection", "handoff"},
            [
                "src/tc_prompt_brain_seq001_v001.py",
                "codex_compat.py",
                ".github/copilot-instructions.md",
            ],
        ),
        (
            {"numeric", "neumeric", "encoding", "file", "files", "identities", "identity", "select"},
            [
                "src/intent_numeric_seq001*.py",
                "src/tc_context_agent_seq001_v004*.py",
            ],
        ),
        (
            {"sim", "sims", "simulate", "simulation", "micro", "rewrite", "rewrites", "compositions", "interlinked"},
            [
                "src/tc_sim_engine_seq001_v004*.py",
                "src/file_self_sim_learning_seq001_v001.py",
                "src/batch_rewrite_sim_seq001_v001.py",
            ],
        ),
        (
            {"intent", "key", "keys", "resolver", "loop", "close", "closed", "approval"},
            [
                "src/tc_intent_keys_seq001_v001.py",
                "src/intent_loop_closer_seq001_v001.py",
                "src/intent_outcome_binder_seq001_v001.py",
            ],
        ),
        (
            {"email", "mail", "narrative", "comedy", "operator", "friend", "beef"},
            [
                "src/file_email_plugin_seq001_v001.py",
                "logs/file_self_sim_learning_email.md",
            ],
        ),
        (
            {"profile", "fingerprint", "name", "nikita", "semantic", "preference", "style"},
            [
                "src/tc_semantic_profile_seq001_v001.py",
                "src/ai_fingerprint_operator_seq001_v001.py",
            ],
        ),
    ]
    out = []
    for terms, candidates in hints:
        if any(term in haystack for term in terms):
            out.extend(_existing_candidates(root, candidates))
    return _dedupe(out)[:8]


def _existing_candidates(root: Path, candidates: list[str]) -> list[str]:
    out = []
    for candidate in candidates:
        if "*" in candidate:
            matches = sorted(root.glob(candidate))
            out.extend(str(path.relative_to(root)).replace("\\", "/") for path in matches if path.is_file())
            continue
        path = root / candidate
        if path.exists():
            out.append(candidate)
    return out


def _files_from_text(text: str) -> list[str]:
    explicit = re.findall(r"(?:src|client|tests?|pigeon_compiler|pigeon_brain)/[a-zA-Z0-9_./\\-]+", str(text))
    stems = re.findall(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+){1,}\b", str(text).lower())
    return _dedupe([item.replace("\\", "/") for item in explicit] + stems)[:8]


def _title(item: dict[str, Any]) -> str:
    text = item.get("you_were_going_to_say", "")
    words = _tokens(text)
    return " ".join(words[:7]) or item.get("source", "unsaid")


def _intent_key(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("intent_key") or "")
    return str(value or "")


def _tokens(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower())
        if len(token) >= 3 and token not in {"the", "and", "for", "with", "that", "this", "you", "are"}
    ]


def _clean(value: Any, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > limit:
        text = text[: limit - 3].rstrip() + "..."
    return text


def _dedupe(values: list[Any]) -> list[Any]:
    out = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(value)
    return out


def _dedupe_threads(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for item in items:
        key = " ".join(_tokens(item.get("you_were_going_to_say", ""))[:12])
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _digest(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except Exception:
        return []
    for line in lines:
        try:
            data = json.loads(line)
        except Exception:
            continue
        if isinstance(data, dict):
            rows.append(data)
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["build_unsaid_thread_digest", "render_unsaid_thread_digest"]
