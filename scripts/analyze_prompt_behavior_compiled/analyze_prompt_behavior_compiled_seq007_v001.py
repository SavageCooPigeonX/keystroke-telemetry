"""analyze_prompt_behavior_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq008_v001 import _compile_bridge
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _emergent_threads(rows: list[PromptRow]) -> list[dict[str, Any]]:
    seed_terms = [
        "intent",
        "keys",
        "profile",
        "audit",
        "artifact",
        "drift",
        "codex",
        "claude",
        "opus",
        "deepseek",
        "files",
        "manifest",
        "hush",
        "thought",
        "completer",
        "reconstruction",
        "brainstorm",
        "research",
    ]
    term_rows: dict[str, list[PromptRow]] = defaultdict(list)
    for row in rows:
        token_set = set(row.tokens)
        for term in seed_terms:
            if term in token_set or term in row.msg.lower():
                term_rows[term].append(row)
    threads = []
    for term, hits in term_rows.items():
        if len(hits) < 3:
            continue
        themes = Counter(t for row in hits for t in row.themes)
        reinf = Counter(row.reinforcement for row in hits)
        first = hits[0]
        last = hits[-1]
        high = sorted(hits, key=lambda r: r.cognitive_load, reverse=True)[:3]
        threads.append(
            {
                "term": term,
                "count": len(hits),
                "first_session": first.session_n,
                "last_session": last.session_n,
                "dominant_themes": themes.most_common(5),
                "reinforcement": dict(reinf),
                "high_load_examples": [
                    {"session_n": row.session_n, "load": row.cognitive_load, "msg": row.msg[:220]}
                    for row in high
                ],
                "compiled_bridge": _compile_bridge(term, hits, themes),
            }
        )
    return sorted(threads, key=lambda item: item["count"], reverse=True)[:18]
