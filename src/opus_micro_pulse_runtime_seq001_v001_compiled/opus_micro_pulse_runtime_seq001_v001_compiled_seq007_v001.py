"""opus_micro_pulse_runtime_seq001_v001_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _folder_for
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _tokens
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import re

def _why_opus_called(rel: str, fragment: str, classification: dict[str, Any]) -> str:
    low = fragment.lower()
    if "manifest" in rel.lower() or "manifest" in low:
        return "manifest state holder for this prompt"
    if "prompt" in rel.lower() or "prompt" in low:
        return "prompt composition and intent-key compiler"
    if "bug" in rel.lower() or "debug" in classification["prompt_class"]:
        return "debug pressure witness"
    if "root" in rel.lower():
        return "root navigation key for called files"
    if "log" in rel.lower():
        return "operator history evidence"
    return f"{classification['prompt_class']} context candidate"


def _mismatch(reason: str, self_claim: str) -> str:
    reason_tokens = set(_tokens(reason))
    claim_tokens = set(_tokens(self_claim))
    if reason_tokens & claim_tokens:
        return "Opus read me mostly correctly."
    return "Opus may be flattening my role; calibrate my syntax triggers before trusting this route."


def _file_solution(rel: str, classification: dict[str, Any], mismatch: str) -> str:
    if "flattening" in mismatch:
        return "increase learned syntax triggers from this prompt if Codex actually touches me"
    if classification["prompt_class"] == "conversation":
        return "log as learning only; do not launch file sim"
    if classification["prompt_class"] == "debug":
        return "route through debug chain and require grader receipt"
    return "keep me in the executor packet only if later pulses still select me"


def _persistent_faults(root: Path, rel: str) -> str:
    bugs = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    hits = [row for row in bugs.get("bugs") or [] if str(row.get("owner") or "") == rel]
    if hits:
        return "; ".join(str(row.get("title") or "open bug") for row in hits[:3])
    syntax = _load_json(root / "logs" / "operator_syntax_triggers.json") or {}
    row = (syntax.get("files") or {}).get(rel) or {}
    if int(row.get("observations") or 0) == 0:
        return "low-touch file; can be missed by Opus unless static syntax matches"
    return f"observations={row.get('observations', 0)}; learned triggers may need backward-pass validation"


def _deepseek_note(rel: str, solution: str) -> str:
    folder = _folder_for(rel)
    return f"Folder manager `{folder}` should store this pulse comment locally and normalize the repair rule: {solution}."
