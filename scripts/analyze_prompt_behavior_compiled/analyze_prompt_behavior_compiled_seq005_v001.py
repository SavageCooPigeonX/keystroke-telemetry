"""analyze_prompt_behavior_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _cooccurrence_graph(rows: list[PromptRow]) -> dict[str, Any]:
    edge_counts: Counter[tuple[str, str]] = Counter()
    bridges: list[dict[str, Any]] = []
    for row in rows:
        unique_themes = sorted(set(row.themes))
        for i, left in enumerate(unique_themes):
            for right in unique_themes[i + 1 :]:
                edge_counts[(left, right)] += 1
        if len(unique_themes) >= 3 or (row.cognitive_load >= 0.5 and len(unique_themes) >= 2):
            bridges.append(
                {
                    "session_n": row.session_n,
                    "ts": row.ts.isoformat(),
                    "themes": unique_themes,
                    "reinforcement": row.reinforcement,
                    "cognitive_load": row.cognitive_load,
                    "msg": row.msg[:360],
                }
            )
    return {
        "top_edges": [
            {"themes": list(edge), "count": count}
            for edge, count in edge_counts.most_common(30)
        ],
        "bridge_prompts": sorted(bridges, key=lambda item: (len(item["themes"]), item["cognitive_load"]), reverse=True)[:30],
    }
