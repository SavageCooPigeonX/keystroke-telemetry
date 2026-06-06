"""file_email_plugin_seq001_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq028_v001 import _plain_snip
from .file_email_plugin_seq001_seq040_v001 import _dedupe_list
from typing import Any
import json
import os
import re

def _codex_prompt_focus_files(
    context: dict[str, Any],
    file_sim: dict[str, Any],
    loop: dict[str, Any],
) -> list[str]:
    out: list[str] = []
    for proposal in file_sim.get("proposals") or []:
        if isinstance(proposal, dict) and proposal.get("path"):
            out.append(str(proposal.get("path")))
    for item in context.get("files") or []:
        if isinstance(item, dict) and item.get("name"):
            out.append(str(item.get("name")))
        elif isinstance(item, str):
            out.append(item)
    for item in loop.get("focus_files") or []:
        if item:
            out.append(str(item))
    out.extend(["logs/prompt_journal.jsonl", "logs/intent_loop_latest.json"])
    return _dedupe_list([item for item in out if item])[:16]


def _codex_prompt_job_id(file_sim: dict[str, Any]) -> str:
    for proposal in file_sim.get("proposals") or []:
        if isinstance(proposal, dict) and proposal.get("deepseek_completion_job_id"):
            return str(proposal.get("deepseek_completion_job_id"))
    return ""


def _codex_prompt_reason(
    prompt_entry: dict[str, Any],
    prompt: str,
    source: str,
    loop: dict[str, Any],
) -> str:
    session_n = prompt_entry.get("session_n")
    loop_id = loop.get("loop_id") or "no_loop_yet"
    preview = _plain_snip(prompt, 260) or "empty prompt"
    return f"Codex prompt receipt from `{source}` session `{session_n}` loop `{loop_id}`: {preview}"
