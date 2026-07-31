"""analyze_prompt_behavior_compiled_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq009_v001 import _infer_failed_response_style
from .analyze_prompt_behavior_compiled_seq009_v001 import _infer_rewarded_response_style
from .analyze_prompt_behavior_compiled_seq012_v001 import _event_type
from .analyze_prompt_behavior_compiled_seq012_v001 import _operator_state
from .analyze_prompt_behavior_compiled_seq013_v001 import _infer_trigger
from .analyze_prompt_behavior_compiled_seq013_v001 import _latent_need
from .analyze_prompt_behavior_compiled_seq014_v001 import _next_response_policy
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _internal_event_log(rows: list[PromptRow]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        previous = rows[max(0, index - 5) : index]
        previous_themes = Counter(t for item in previous for t in item.themes)
        correction_modes = _infer_failed_response_style(row, previous)
        reward_modes = _infer_rewarded_response_style(row, previous)
        event_type = _event_type(row)
        events.append(
            {
                "schema": "operator_behavior_event/v1",
                "session_n": row.session_n,
                "ts": row.ts.isoformat(),
                "event_type": event_type,
                "operator_state": _operator_state(row),
                "reinforcement": row.reinforcement,
                "cognitive_load": row.cognitive_load,
                "surface_text": row.msg,
                "deleted_words": row.raw.get("deleted_words") or [],
                "themes": row.themes,
                "preceding_context_themes": previous_themes.most_common(6),
                "inferred_trigger": _infer_trigger(row, previous),
                "punished_response_style": correction_modes if event_type in {"punishment", "mixed", "correction"} else [],
                "rewarded_response_style": reward_modes if event_type in {"reward", "mixed"} else [],
                "latent_need": _latent_need(row, correction_modes, reward_modes),
                "next_response_policy": _next_response_policy(row, correction_modes, reward_modes),
                "evidence": {
                    "signals": row.raw.get("signals") or {},
                    "intent_label": row.raw.get("intent"),
                    "cognitive_state_label": row.raw.get("cognitive_state"),
                    "previous_prompts": [
                        {
                            "session_n": item.session_n,
                            "reinforcement": item.reinforcement,
                            "themes": item.themes,
                            "msg": item.msg[:240],
                        }
                        for item in previous[-3:]
                    ],
                },
            }
        )
    return events
