"""codex_compat_render_state_markdown_seq058_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 058 | VER: v002 | 150 lines | ~1,587 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_parse_deleted_words_seq003_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _parse_deleted_words
from typing import Any
import json
import os
import re

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
