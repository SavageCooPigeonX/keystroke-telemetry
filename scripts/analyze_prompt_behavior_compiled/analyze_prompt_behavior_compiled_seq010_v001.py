"""analyze_prompt_behavior_compiled_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq008_v001 import _context_window
from .analyze_prompt_behavior_compiled_seq009_v001 import _infer_failed_response_style
from .analyze_prompt_behavior_compiled_seq009_v001 import _infer_rewarded_response_style
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _behavioral_events(rows: list[PromptRow]) -> dict[str, Any]:
    punishments: list[dict[str, Any]] = []
    rewards: list[dict[str, Any]] = []
    mixed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        previous = rows[max(0, index - 3) : index]
        base = {
            "session_n": row.session_n,
            "ts": row.ts.isoformat(),
            "reinforcement": row.reinforcement,
            "cognitive_load": row.cognitive_load,
            "themes": row.themes,
            "msg": row.msg[:360],
            "deleted_words": row.raw.get("deleted_words") or [],
            "context": _context_window(rows, index),
        }
        if row.reinforcement in {"negative", "negative_soft"}:
            punishments.append(base | {"inferred_failed_response_style": _infer_failed_response_style(row, previous)})
        elif row.reinforcement == "positive":
            rewards.append(base | {"inferred_rewarded_response_style": _infer_rewarded_response_style(row, previous)})
        elif row.reinforcement == "mixed":
            mixed.append(
                base
                | {
                    "inferred_failed_response_style": _infer_failed_response_style(row, previous),
                    "inferred_rewarded_response_style": _infer_rewarded_response_style(row, previous),
                }
            )
    return {
        "punishment_events": sorted(punishments, key=lambda item: item["cognitive_load"], reverse=True)[:40],
        "reward_events": sorted(rewards, key=lambda item: item["cognitive_load"], reverse=True)[:40],
        "mixed_events": sorted(mixed, key=lambda item: item["cognitive_load"], reverse=True)[:20],
        "punishment_mode_counts": Counter(
            mode
            for item in punishments
            for mode in item.get("inferred_failed_response_style", [])
        ).most_common(),
        "reward_mode_counts": Counter(
            mode
            for item in rewards
            for mode in item.get("inferred_rewarded_response_style", [])
        ).most_common(),
    }
