"""file_email_plugin_seq001_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq017_v001 import _policy_mail_line
from .file_email_plugin_seq001_seq018_v001 import _learning_packet_summary
from .file_email_plugin_seq001_seq018_v001 import _learning_validation_plan
from .file_email_plugin_seq001_seq019_v001 import _learning_context_from_record
from .file_email_plugin_seq001_seq019_v001 import _learning_current_work
from .file_email_plugin_seq001_seq020_v001 import _learning_profile_signal_line
from .file_email_plugin_seq001_seq020_v001 import _learning_story_lessons
from .file_email_plugin_seq001_seq021_v001 import _learning_story_quotes
from .file_email_plugin_seq001_seq022_v001 import _learning_story_cast
from .file_email_plugin_seq001_seq022_v001 import _learning_story_deepseek
from .file_email_plugin_seq001_seq022_v001 import _learning_story_grader
from .file_email_plugin_seq001_seq023_v001 import _learning_closing_scene
from pathlib import Path
from typing import Any
import json
import os
import re

def render_learning_digest_email(record: dict[str, Any]) -> str:
    digest = record.get("learning_digest") if isinstance(record.get("learning_digest"), dict) else {}
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    policy = record.get("operator_response_policy") if isinstance(record.get("operator_response_policy"), dict) else {}
    wake_order = digest.get("wake_order") if isinstance(digest.get("wake_order"), list) else []
    packets = digest.get("packets") if isinstance(digest.get("packets"), list) else []
    top = wake_order[0] if wake_order else {}
    second = wake_order[1] if len(wake_order) > 1 else {}
    third = wake_order[2] if len(wake_order) > 2 else {}
    validation = _learning_validation_plan(packets)
    context = _learning_context_from_record(record)
    current = _learning_current_work(record) or operator.get("current_work") or "make the files earn their own rewrite"
    profile_note = _learning_profile_signal_line(record, operator)
    woke_files = ", ".join(
        str(item.get("file") or "")
        for item in wake_order[:6]
        if isinstance(item, dict) and item.get("file")
    ) or "none"
    lines = [
        f"From: {record.get('file')}",
        "To: Nikita",
        f"Subject: {record.get('subject', '')}",
        "",
        "Nikita,",
        "",
        _policy_mail_line(policy),
        "",
        f"File room: `{record.get('file')}`",
        "Blank sheet: learning-only; no source overwrite happened.",
        f"Woke files -> {woke_files}",
        "Text back like a message: `remember: ...`, `use: ...`, `avoid: ...`, `style: ...`",
        "",
        "The repo called an emergency rewrite meeting and immediately lied about being ready.",
        "",
        f"`{Path(str(top.get('file') or 'the top file')).name}` kicked the door open first because `{top.get('wake_reason', 'the intent math pointed at it')}`.",
    ]
    if second:
        lines.append(
            f"`{Path(str(second.get('file'))).name}` followed with a stack of receipts and the facial expression of a file that has seen a stale context pack ruin lunch."
        )
    if third:
        lines.append(
            f"`{Path(str(third.get('file'))).name}` said it was just here to help, which everyone correctly understood as a threat to reorganize the room."
        )
    lines.extend([
        "",
        "Then the grader walked in, stole the marker, and wrote one sentence on the board:",
        "",
        "\"No overwrite until the validation packet can survive daylight.\"",
        "",
        "That is the master plan. The grader is not comic relief. The grader is the bouncer, the accountant, and the little courtroom in the wall. Every file can monologue. Only the grader gets to say whether the monologue becomes source.",
        "",
        "What I think you are actually doing:",
        f"{current}.",
    ])
    if profile_note:
        lines.extend(["", profile_note])
    lines.extend([
        "",
        "What the files learned while arguing:",
        *_learning_story_lessons(wake_order, packets),
        "",
        "Overheard in the file room:",
        *_learning_story_quotes(wake_order, packets),
        "",
        "Who wants the next job:",
        *_learning_story_cast(wake_order, packets),
        "",
        "What DeepSeek should receive, if we let it near the keyboard:",
        *_learning_story_deepseek(packets, context, validation),
        "",
        "What the grader will accept:",
        *_learning_story_grader(validation),
        "",
        "I need from you:",
        "What I need from you, not as a form, as control:",
        "- `approve: draft tests` if the next move is letting the files write their own proof.",
        "- `use: path/to/file.py` if a context vein is missing and you want it loaded every time.",
        "- `avoid: stale committee email` if this voice starts wearing a blazer again.",
        "- `style: narrative comedy, files have grudges, grader has veto` if this is the lane.",
        "",
        "Routing crumbs under the floorboards:",
        f"- intent: `{record.get('intent_key') or 'none'}`",
        f"- context request: `{(record.get('context_request') or {}).get('request_id', 'none')}`",
        f"- learning packets: `{_learning_packet_summary(packets)}`",
        f"- latest sim: `{(digest.get('paths') or {}).get('latest', 'logs/file_self_sim_learning_latest.json')}`",
        f"- profile memory: `file_profiles.json`",
        "",
        "Closing scene:",
        _learning_closing_scene(wake_order, packets),
        "",
    ])
    return "\n".join(lines)
