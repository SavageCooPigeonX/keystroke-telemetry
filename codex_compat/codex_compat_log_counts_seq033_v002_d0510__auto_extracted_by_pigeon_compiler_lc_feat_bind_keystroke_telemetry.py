"""codex_compat_log_counts_seq033_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 033 | VER: v002 | 38 lines | ~268 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import json
import os
import re

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
