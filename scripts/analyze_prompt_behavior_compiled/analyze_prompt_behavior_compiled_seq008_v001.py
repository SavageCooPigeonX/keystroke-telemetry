"""analyze_prompt_behavior_compiled_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _compile_bridge(term: str, hits: list[PromptRow], themes: Counter[str]) -> str:
    first_theme = themes.most_common(1)[0][0] if themes else "unclassified"
    last = hits[-1].msg[:120]
    return (
        f"{term} behaves like a bridge through {first_theme}: it starts as repeated surface language, "
        f"then reappears under higher load as a routing demand. Latest trace: {last}"
    )


def _mode_matches(text: str, patterns: dict[str, str]) -> list[str]:
    return [name for name, pattern in patterns.items() if re.search(pattern, text, re.IGNORECASE)]


def _context_window(rows: list[PromptRow], index: int, before: int = 3, after: int = 1) -> dict[str, Any]:
    prev_rows = rows[max(0, index - before) : index]
    next_rows = rows[index + 1 : index + 1 + after]
    return {
        "previous": [
            {
                "session_n": item.session_n,
                "reinforcement": item.reinforcement,
                "themes": item.themes,
                "load": item.cognitive_load,
                "msg": item.msg[:220],
            }
            for item in prev_rows
        ],
        "next": [
            {
                "session_n": item.session_n,
                "reinforcement": item.reinforcement,
                "themes": item.themes,
                "load": item.cognitive_load,
                "msg": item.msg[:180],
            }
            for item in next_rows
        ],
    }
