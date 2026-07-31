"""analyze_prompt_behavior_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _theme_reinforcement(rows: list[PromptRow]) -> dict[str, Any]:
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for theme in row.themes or ["unclassified"]:
            stats[theme][row.reinforcement] += 1
            if row.reinforcement != "neutral" and len(examples[theme][row.reinforcement]) < 5:
                examples[theme][row.reinforcement].append(
                    {
                        "session_n": row.session_n,
                        "ts": row.ts.isoformat(),
                        "load": row.cognitive_load,
                        "msg": row.msg[:260],
                    }
                )
    result = {}
    for theme, counter in sorted(stats.items()):
        total = sum(counter.values())
        result[theme] = {
            "total": total,
            "positive": counter.get("positive", 0),
            "negative": counter.get("negative", 0) + counter.get("negative_soft", 0),
            "mixed": counter.get("mixed", 0),
            "neutral": counter.get("neutral", 0),
            "positive_rate": round(counter.get("positive", 0) / total, 4) if total else 0,
            "negative_rate": round((counter.get("negative", 0) + counter.get("negative_soft", 0)) / total, 4) if total else 0,
            "examples": examples.get(theme, {}),
        }
    return result
