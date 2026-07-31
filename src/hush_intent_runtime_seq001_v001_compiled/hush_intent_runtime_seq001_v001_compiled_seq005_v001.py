"""hush_intent_runtime_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq006_v001 import _files_for_move
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _snip
from typing import Any
import re

def _intent_moves(prompt: str, graph: dict[str, Any]) -> list[dict[str, Any]]:
    lower = prompt.lower()
    specs = [
        ("hush_intent_runtime", {"hush", "runtime", "reconstruction", "persistent", "intent map"}),
        ("repo_classification", {"repo", "root", "context0", "linkrouter", "maif", "codebase"}),
        ("linkrouter_file_room_access", {"linkrouter", "maif", "files", "call files"}),
        ("file_mail_quality_gate", {"email", "emails", "mail", "text"}),
        ("file_identity_narrative", {"rename", "identity", "inator", "names", "responsible"}),
        ("field_whisper_irt_future_layer", {"whisper", "irt", "field", "intent"}),
    ]
    moves = []
    for name, hints in specs:
        if any(hint in lower for hint in hints):
            moves.append(_move(name, prompt))
    if not moves:
        for item in (graph.get("intents") or [])[:4]:
            moves.append({
                "name": str(item.get("target") or "intent_move"),
                "intent_key": str(item.get("intent_key") or "hush:route:intent_move:minor"),
                "summary": str(item.get("segment") or item.get("why") or "intent graph move"),
                "files": item.get("files") or [],
            })
    return moves[:8] or [_move("general_intent_reconstruction", prompt)]


def _move(name: str, prompt: str) -> dict[str, Any]:
    return {
        "name": name,
        "intent_key": f"hush:build:{name}:patch",
        "summary": _summary_for_move(name, prompt),
        "files": _files_for_move(name),
    }


def _summary_for_move(name: str, prompt: str) -> str:
    summaries = {
        "hush_intent_runtime": "make Hush own persistent intent reconstruction and extended runtime state",
        "repo_classification": "classify active repo before manifest scoring and block unsafe mutation",
        "linkrouter_file_room_access": "treat LinkRouter/MAIF fingerprints as callable repo-room context",
        "file_mail_quality_gate": "stop emails that do not carry learned/done/next/need signal",
        "file_identity_narrative": "make file packets expose identity, responsibility, and mutation state",
        "field_whisper_irt_future_layer": "reserve live field intent whisper hooks for non-coding IRT",
    }
    return summaries.get(name, _snip(prompt, 180))
