"""opus_prompt_box_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq005_v001 import _upsert
from .opus_prompt_box_seq001_v001_compiled_seq007_v001 import _problem_from_intent
from .opus_prompt_box_seq001_v001_compiled_seq008_v001 import _problem_from_bug
from .opus_prompt_box_seq001_v001_compiled_seq008_v001 import _problem_from_candidate
from .opus_prompt_box_seq001_v001_compiled_seq009_v001 import _problem_from_prompt
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _problem_key
from typing import Any
import re

def _merge_problems(
    prompt: str,
    intent_graph: dict[str, Any],
    bugs: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    absorbed: list[dict[str, Any]],
    now: str,
) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in absorbed:
        key = _problem_key(row)
        by_key[key] = row
    for intent in intent_graph.get("intents") or []:
        if intent.get("void"):
            continue
        row = _problem_from_intent(intent, prompt, now)
        key = _problem_key(row)
        by_key[key] = _upsert(by_key.get(key), row, now)
    for bug in bugs:
        row = _problem_from_bug(bug, now)
        key = _problem_key(row)
        by_key[key] = _upsert(by_key.get(key), row, now)
    for cand in candidates:
        row = _problem_from_candidate(cand, now)
        key = _problem_key(row)
        by_key[key] = _upsert(by_key.get(key), row, now)
    if prompt and not by_key:
        row = _problem_from_prompt(prompt, intent_graph, now)
        by_key[_problem_key(row)] = row
    return list(by_key.values())
