"""codex_compat_running_prompt_summary_seq024_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v002 | 35 lines | ~363 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_load_jsonl_tail_seq007_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_jsonl_tail
from pathlib import Path
from typing import Any
import json
import os
import re

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
