"""codex_compat_run_pre_prompt_from_composition_seq054_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 054 | VER: v002 | 122 lines | ~1,699 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_build_dynamic_context_pack_seq042_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import build_dynamic_context_pack
from .codex_compat_emit_codex_prompt_email_seq046_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _emit_codex_prompt_email
from .codex_compat_ensure_repo_on_path_seq009_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _ensure_repo_on_path
from .codex_compat_fire_file_sim_seq044_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _fire_file_sim
from .codex_compat_inject_pre_prompt_state_seq022_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _inject_pre_prompt_state
from .codex_compat_latest_json_seq019_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _latest_json
from .codex_compat_load_json_seq059_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_json
from .codex_compat_parse_deleted_words_seq003_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _parse_deleted_words
from .codex_compat_record_intent_loop_seq045_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _record_intent_loop
from .codex_compat_refresh_state_seq057_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import refresh_state
from .codex_compat_render_pre_prompt_block_seq021_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _render_pre_prompt_block
from .codex_compat_run_sim_buffer_seq018_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _run_sim_buffer
from .codex_compat_select_context_seq056_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import select_context
from .codex_compat_utc_now_seq001_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _utc_now
from pathlib import Path
from typing import Any
import json
import os
import re

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
