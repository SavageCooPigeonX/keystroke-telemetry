"""codex_compat_run_pre_prompt_pipeline_seq055_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 055 | VER: v002 | 158 lines | ~1,887 tokens
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
from .codex_compat_log_composition_seq063_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import log_composition
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
