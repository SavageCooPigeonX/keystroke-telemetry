"""file_email_plugin_seq001_seq020_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq028_v001 import _plain_snip
from pathlib import Path
from typing import Any
import re

def _learning_profile_signal_line(record: dict[str, Any], operator: dict[str, Any]) -> str:
    latest = _plain_snip(operator.get("latest_operator_text"), 220)
    if not latest:
        return ""
    digest = record.get("learning_digest") if isinstance(record.get("learning_digest"), dict) else {}
    raw = str(digest.get("raw_intent") or "")
    if raw and _token_overlap_ratio(raw, latest) < 0.25:
        return f"Profile cache note: \"{latest}\" looks stale for this sim, so the files ignored it and used the live intent."
    return f"Latest operator signal: \"{latest}\""


def _token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(left).lower()))
    right_tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(right).lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, min(len(left_tokens), len(right_tokens)))


def _learning_story_lessons(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[str]:
    lessons = []
    if wake_order:
        top = wake_order[0]
        lessons.append(
            f"- `{Path(str(top.get('file'))).name}` learned it is the first suspect, not the hero. Wake score `{top.get('wake_score')}` buys attention, not permission."
        )
    if packets:
        first_packet = packets[0]
        readiness = first_packet.get("overwrite_readiness") if isinstance(first_packet.get("overwrite_readiness"), dict) else {}
        lessons.append(
            f"- `{Path(str(first_packet.get('file'))).name}` tried to sound rewrite-ready. The grader read `{readiness.get('state', 'unknown')}` and put the chair back under the table."
        )
    if len(packets) > 1:
        lessons.append(
            f"- `{len(packets)}` files now have packet-shaped memory. That means future prompts can reuse scars instead of rediscovering the same rake."
        )
    if not lessons:
        lessons.append("- The meeting learned nothing, which is useful because now candidate selection is the problem.")
    return lessons[:4]
