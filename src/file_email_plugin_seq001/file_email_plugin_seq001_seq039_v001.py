"""file_email_plugin_seq001_seq039_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq031_v001 import _inline_quote
from .file_email_plugin_seq001_seq040_v001 import _top_counts
from typing import Any
import re

def _render_file_memory(memory: dict[str, Any]) -> str:
    knowledge = memory.get("knowledge") if isinstance(memory.get("knowledge"), dict) else {}
    lines = [
        "# File Mail Memory",
        "",
        f"- file: `{memory.get('file')}`",
        f"- thread_id: `{memory.get('thread_id')}`",
        f"- updated_at: `{memory.get('updated_at', memory.get('created_at', ''))}`",
        f"- messages: `{len(memory.get('messages') or [])}`",
        "",
        "## What This File Knows",
        "",
        f"- current work: {knowledge.get('last_current_work') or 'unknown'}",
        f"- latest operator signal: {_inline_quote(knowledge.get('last_operator_signal') or '', 260)}",
        f"- preferred context: `{', '.join((knowledge.get('preferred_context') or [])[:12]) or 'none'}`",
        f"- avoid: `{', '.join((knowledge.get('avoid_rules') or [])[:12]) or 'none'}`",
        f"- style: `{', '.join((knowledge.get('style_notes') or [])[:8]) or 'adaptive mail'}`",
        "",
        "## Counts",
        "",
        f"- operator intents: `{_top_counts(knowledge.get('operator_intents'))}`",
        f"- intent keys: `{_top_counts(knowledge.get('intent_keys'))}`",
        f"- neighbors: `{_top_counts(knowledge.get('neighbors'))}`",
        f"- failed checks: `{_top_counts(knowledge.get('failed_checks'))}`",
        "",
        "## Notes From Replies",
        "",
    ]
    notes = knowledge.get("operator_notes") or []
    lines.extend(f"- {note}" for note in notes[-12:]) if notes else lines.append("- none yet")
    lines.extend(["", "## Recent Messages", ""])
    for msg in (memory.get("messages") or [])[-8:]:
        lines.extend([
            f"### {msg.get('ts')} - {msg.get('direction')} - {msg.get('subject', '')}",
            "",
            str(msg.get("body_preview") or msg.get("body") or "")[:900],
            "",
        ])
    return "\n".join(lines)
