"""analyze_prompt_behavior_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from statistics import mean
from typing import Any
import re

def _bucket_by_day(rows: list[PromptRow]) -> list[dict[str, Any]]:
    groups: dict[str, list[PromptRow]] = defaultdict(list)
    for row in rows:
        groups[row.ts.date().isoformat()].append(row)
    buckets = []
    for day, group in sorted(groups.items()):
        counts = Counter(r.reinforcement for r in group)
        theme_counts = Counter(t for r in group for t in r.themes)
        buckets.append(
            {
                "day": day,
                "prompts": len(group),
                "avg_cognitive_load": round(mean(r.cognitive_load for r in group), 4),
                "reinforcement": dict(counts),
                "top_themes": theme_counts.most_common(6),
                "high_load_sessions": [
                    {"session_n": r.session_n, "load": r.cognitive_load, "msg": r.msg[:180]}
                    for r in sorted(group, key=lambda item: item.cognitive_load, reverse=True)[:3]
                ],
            }
        )
    return buckets
