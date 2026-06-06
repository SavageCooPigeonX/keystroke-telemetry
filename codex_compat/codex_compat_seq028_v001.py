"""codex_compat_seq028_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _parse_deleted_words
from .codex_compat_seq001_v001 import _utc_now
from .codex_compat_seq002_v001 import _ensure_repo_on_path
from .codex_compat_seq007_v001 import _latest_json
from .codex_compat_seq007_v001 import _run_sim_buffer
from .codex_compat_seq008_v001 import _render_pre_prompt_block
from .codex_compat_seq009_v001 import _inject_pre_prompt_state
from .codex_compat_seq022_v001 import build_dynamic_context_pack
from .codex_compat_seq024_v001 import _fire_file_sim
from .codex_compat_seq025_v001 import _emit_codex_prompt_email
from .codex_compat_seq025_v001 import _record_intent_loop
from .codex_compat_seq030_v001 import select_context
from .codex_compat_seq031_v001 import refresh_state
from .codex_compat_seq033_v001 import _load_json
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
