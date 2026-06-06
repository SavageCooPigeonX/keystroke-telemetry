"""codex_compat_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _load_jsonl_tail
from .codex_compat_seq033_v001 import _load_json
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
