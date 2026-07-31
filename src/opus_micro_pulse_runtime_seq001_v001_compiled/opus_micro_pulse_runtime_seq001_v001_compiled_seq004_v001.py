"""opus_micro_pulse_runtime_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq005_v001 import _explicit_runtime_files
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _intent_keys
from pathlib import Path
from src.operator_syntax_triggers_seq001_v001 import match_operator_syntax_triggers
from typing import Any
import json
import re

def _composition_fragments(prompt: str, row: dict[str, Any], *, max_pulses: int) -> list[str]:
    rewrites = row.get("rewrites") or []
    fragments = []
    for rewrite in rewrites[-max_pulses:]:
        new = str(rewrite.get("new") or "").strip()
        if len(new) >= 24:
            fragments.append(new)
    if not fragments:
        words = prompt.split()
        if not words:
            return [""]
        for pct in (0.35, 0.7, 1.0):
            take = max(1, min(len(words), int(len(words) * pct)))
            fragments.append(" ".join(words[:take]))
    fragments.append(prompt)
    out: list[str] = []
    for frag in fragments:
        frag = frag.strip()
        if frag and frag not in out:
            out.append(frag)
    return out[-max_pulses:] or [prompt]


def _select_files(root: Path, fragment: str, classification: dict[str, Any], *, file_limit: int) -> list[str]:
    syntax = match_operator_syntax_triggers(root, fragment, intent_key=" ".join(_intent_keys(fragment, classification)), limit=file_limit)
    files = [str(row.get("file") or "") for row in syntax if row.get("file")]
    files.extend(_explicit_runtime_files(fragment))
    if classification["prompt_class"] in {"debug", "directive"}:
        files.extend([
            "src/opus_micro_pulse_runtime_seq001_v001.py",
            "src/root_sim_key_file_seq001_v001.py",
            "src/unified_manifest_state_seq001_v001.py",
        ])
    if classification["prompt_class"] in {"conversation", "correction", "exploration"}:
        files.extend([
            "logs/prompt_journal.jsonl",
            "logs/operator_syntax_triggers.json",
        ])
    return [rel for rel in dict.fromkeys(files) if rel][:file_limit]
