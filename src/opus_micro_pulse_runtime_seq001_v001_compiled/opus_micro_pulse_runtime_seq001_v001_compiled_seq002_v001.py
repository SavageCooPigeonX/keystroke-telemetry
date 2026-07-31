"""opus_micro_pulse_runtime_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _class_priority
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _epistemic_status
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _tokens
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import PROMPT_CLASSES
from typing import Any
import re

def classify_prompt(text: str) -> dict[str, Any]:
    tokens = set(_tokens(text))
    scores: dict[str, int] = {}
    for name, spec in PROMPT_CLASSES.items():
        scores[name] = len(tokens & set(spec["tokens"]))
    if re.search(r"\b(build|implement|execute|do that|go ahead|make sure)\b", text, re.I):
        scores["directive"] += 4
    if re.search(r"\b(debug|bug|stale|wrong|failing|cutoff|broken)\b", text, re.I):
        scores["debug"] += 3
    if re.search(r"\b(audit|review|assess|grade)\b", text, re.I):
        scores["audit"] += 3
    if re.search(r"\b(what if|maybe|imagine|theory|could)\b", text, re.I):
        scores["exploration"] += 2
    if re.search(r"\b(hate|stupid|wrong|opposite|not quite|frustrat)\w*\b", text, re.I):
        scores["correction"] += 3
    if re.search(r"\b(plan|architecture|workflow|system|contract)\b", text, re.I):
        scores["planning"] += 2
    prompt_class = max(scores, key=lambda key: (scores[key], _class_priority(key)))
    spec = PROMPT_CLASSES[prompt_class]
    return {
        "prompt_class": prompt_class,
        "sim_policy": spec["policy"],
        "durable_mutation_allowed": bool(spec["mutates"]),
        "scores": scores,
        "epistemic_status": _epistemic_status(prompt_class),
    }
