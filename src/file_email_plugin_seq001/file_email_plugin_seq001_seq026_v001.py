"""file_email_plugin_seq001_seq026_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq027_v001 import _first_validation
from .file_email_plugin_seq001_seq027_v001 import _memory_knowledge
from .file_email_plugin_seq001_seq027_v001 import _preferred_context
from pathlib import Path
from typing import Any
import re

def _planning_lines(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> list[str]:
    knowledge = _memory_knowledge(memory)
    lines = []
    if failed_checks:
        lines.append(f"Fix `{failed_checks[0].get('key', 'unknown')}` before pretending this loop is complete.")
    context = _preferred_context(record, knowledge)
    if context:
        lines.append("Load " + ", ".join(f"`{item}`" for item in context[:4]) + " before a rewrite.")
    validation = _first_validation(record)
    if validation != "ask for context before rewrite":
        lines.append(f"Run `{validation}` after approval.")
    lines.append("Keep the next visible email to learned / done / next / ask, with the machine paperwork stored behind it.")
    lines.append(f"Let `{Path(file_path).name}` update its memory from replies before the next sim.")
    return lines[:5]


def _need_lines(
    file_path: str,
    record: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> list[str]:
    lines = []
    if failed_checks:
        lines.append(f"Reply `remember: {failed_checks[0].get('key', 'failed_check')} means not done yet` if that rule should persist.")
    if not (record.get("context_injection") or []):
        lines.append("Reply `use: path/to/file.py` to pin the next context pack.")
    lines.append("Reply `avoid: generic status memo` if the voice slips back into dashboard sludge.")
    lines.append("Reply `style: old friend, specific, a little unhinged, never vague` to tune the file's future mail.")
    return lines[:4]
