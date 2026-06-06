"""file_email_plugin_seq001_seq024_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq027_v001 import _memory_knowledge
from .file_email_plugin_seq001_seq028_v001 import _plain_snip
from pathlib import Path
from typing import Any
import re

def _learned_lines(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
) -> list[str]:
    knowledge = _memory_knowledge(memory)
    lines = []
    current = operator.get("current_work")
    latest = _plain_snip(operator.get("latest_operator_text"), 160)
    if current:
        lines.append(f"Your actual move is `{current}`.")
    if latest:
        lines.append(f"Latest signal: \"{latest}\"")
    comment = _plain_snip(record.get("file_comment"), 180)
    if comment:
        lines.append(f"My file comment: \"{comment}\"")
    for note in _useful_memory_notes(knowledge)[-2:]:
        lines.append(f"I remember: {note}.")
    for avoid in (knowledge.get("avoid_rules") or [])[-2:]:
        lines.append(f"Do not do this: {avoid}.")
    for style in (knowledge.get("style_notes") or [])[-1:]:
        lines.append(f"Style pressure: {style}.")
    if not lines:
        lines.append(f"`{Path(file_path).name}` has no durable lessons yet, so this message starts the thread.")
    return lines[:5]


def _useful_memory_notes(knowledge: dict[str, Any]) -> list[str]:
    junk = {"done", "next", "and ask", "ask"}
    notes = []
    for note in knowledge.get("operator_notes") or []:
        text = str(note or "").strip()
        if not text or text.lower() in junk or len(text) < 10:
            continue
        notes.append(text)
    return notes
