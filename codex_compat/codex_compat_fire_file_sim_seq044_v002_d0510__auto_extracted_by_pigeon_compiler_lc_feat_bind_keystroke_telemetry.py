"""codex_compat_fire_file_sim_seq044_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 044 | VER: v002 | 48 lines | ~444 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_ensure_repo_on_path_seq009_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import os
import re

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
        from src.batch_rewrite_sim_seq001_v002_d0510__proposal_only_batch_rewrite_simulator_lc_feat_bind_keystroke_telemetry import (
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
