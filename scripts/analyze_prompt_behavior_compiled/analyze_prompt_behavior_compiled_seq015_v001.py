"""analyze_prompt_behavior_compiled_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq008_v001 import _mode_matches
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from statistics import mean
from typing import Any
import re

def _correction_chains(rows: list[PromptRow]) -> list[dict[str, Any]]:
    chains: list[list[PromptRow]] = []
    current: list[PromptRow] = []
    for row in rows:
        is_correction = row.reinforcement in {"negative", "negative_soft", "mixed"} or row.cognitive_load >= 0.58
        if is_correction:
            current.append(row)
        else:
            if len(current) >= 2:
                chains.append(current)
            current = []
    if len(current) >= 2:
        chains.append(current)

    out = []
    for chain in chains:
        text = " ".join(item.msg for item in chain)
        out.append(
            {
                "start_session": chain[0].session_n,
                "end_session": chain[-1].session_n,
                "duration_prompts": len(chain),
                "avg_load": round(mean(item.cognitive_load for item in chain), 4),
                "themes": Counter(t for item in chain for t in item.themes).most_common(8),
                "correction_modes": Counter(
                    mode
                    for mode in _mode_matches(text, CORRECTION_MODES)
                ).most_common(),
                "operator_log": _chain_logline(chain),
                "evidence": [
                    {"session_n": item.session_n, "load": item.cognitive_load, "msg": item.msg[:260]}
                    for item in chain[:6]
                ],
            }
        )
    return sorted(out, key=lambda item: (item["avg_load"], item["duration_prompts"]), reverse=True)[:25]


def _chain_logline(chain: list[PromptRow]) -> str:
    themes = Counter(t for item in chain for t in item.themes).most_common(3)
    first = chain[0].msg[:120]
    last = chain[-1].msg[:120]
    return (
        f"Correction chain {chain[0].session_n}->{chain[-1].session_n}: "
        f"operator load stayed elevated around {themes}. Initial signal: {first} Latest correction: {last}"
    )
