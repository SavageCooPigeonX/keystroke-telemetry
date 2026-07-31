"""analyze_prompt_behavior_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from statistics import mean
from typing import Any
import re

def _shift_points(rows: list[PromptRow], window: int) -> list[dict[str, Any]]:
    if len(rows) < window * 2:
        return []
    shifts = []
    for idx in range(window, len(rows) - window):
        before = rows[idx - window : idx]
        after = rows[idx : idx + window]
        load_delta = mean(r.cognitive_load for r in after) - mean(r.cognitive_load for r in before)
        before_themes = Counter(t for r in before for t in r.themes)
        after_themes = Counter(t for r in after for t in r.themes)
        theme_delta = {
            theme: after_themes.get(theme, 0) - before_themes.get(theme, 0)
            for theme in sorted(set(before_themes) | set(after_themes))
        }
        top_delta = sorted(theme_delta.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        if abs(load_delta) >= 0.07 or any(abs(v) >= max(4, window // 5) for _, v in top_delta):
            row = rows[idx]
            shifts.append(
                {
                    "at_session": row.session_n,
                    "ts": row.ts.isoformat(),
                    "load_delta": round(load_delta, 4),
                    "top_theme_delta": top_delta,
                    "msg": row.msg[:240],
                }
            )
    # Keep separated shift points so the report is readable.
    filtered = []
    last_session = -999
    for item in sorted(shifts, key=lambda x: abs(x["load_delta"]) + sum(abs(v) for _, v in x["top_theme_delta"]) / 20, reverse=True):
        if abs(item["at_session"] - last_session) < max(8, window // 2):
            continue
        filtered.append(item)
        last_session = item["at_session"]
        if len(filtered) >= 12:
            break
    return sorted(filtered, key=lambda x: x["at_session"])
