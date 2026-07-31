"""opus_prompt_box_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DROP_STATUS
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import MAX_OPEN_PROBLEMS
from typing import Any
import re

def render_opus_prompt_box(box: dict[str, Any]) -> str:
    lines = [
        "# Opus Prompt Box",
        "",
        f"- writer: `{box.get('writer', 'claude-opus')}`",
        f"- open problems: `{box.get('open_count', 0)}` / `{box.get('max_open', MAX_OPEN_PROBLEMS)}`",
        f"- tax dropped this pass: `{box.get('dropped_count', 0)}`",
        "",
        "## Operator Prompt",
        box.get("operator_prompt") or "(none)",
        "",
        "## How Opus Routes This Prompt",
        box.get("routing_note") or "",
        "",
        "## Intent Routes",
    ]
    for row in box.get("intent_routes") or []:
        lines.append(
            f"- `{row.get('intent_key')}` domain=`{row.get('domain_id')}` "
            f"score=`{row.get('confidence', 0)}` files={len(row.get('files') or [])}"
        )
    lines.extend(["", "## Open Problems (refined this prompt)"])
    for row in box.get("open_problems") or []:
        lines.append(
            f"- `{row.get('id')}` **{row.get('title')}** "
            f"| intent=`{row.get('intent_key')}` | score=`{round(float(row.get('priority_score') or 0), 3)}` "
            f"| tax=`{round(float(row.get('tax_factor') or 1), 3)}` | hits=`{row.get('prompt_hits', 0)}`"
        )
        if row.get("focus_files"):
            lines.append(f"  - focus: {', '.join(row['focus_files'][:4])}")
    if box.get("tax_dropped"):
        lines.extend(["", "## Tax Dropped (over cap or stale)"])
        for row in box["tax_dropped"][:8]:
            lines.append(f"- `{row.get('id')}` {row.get('title')} -> {row.get('drop_reason', DROP_STATUS)}")
    return "\n".join(lines) + "\n"
