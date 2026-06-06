"""file_email_plugin_seq001_seq021_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq018_v001 import _learning_validation_plan
from pathlib import Path
from typing import Any
import os
import re

def _learning_story_quotes(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[str]:
    packet_by_file = {
        str(packet.get("file")): packet
        for packet in packets
        if isinstance(packet, dict) and packet.get("file")
    }
    quotes = []
    for node in wake_order[:8]:
        file_path = str(node.get("file") or "unknown")
        packet = packet_by_file.get(file_path, {})
        role = str(node.get("role") or "learner")
        validation = _learning_validation_plan([packet]) if packet else []
        readiness = packet.get("overwrite_readiness") if isinstance(packet.get("overwrite_readiness"), dict) else {}
        quote = _file_state_quote(file_path, role, validation, readiness, node)
        quotes.append(f"- `{Path(file_path).name}`: \"{quote}\"")
    return quotes or ["- `orchestrator`: \"No file spoke. The selector is standing in the corner pretending that was a strategy.\""]


def _file_state_quote(
    file_path: str,
    role: str,
    validation: list[str],
    readiness: dict[str, Any],
    node: dict[str, Any],
) -> str:
    name = Path(file_path).name
    gate = validation[0] if validation else str(node.get("next_question") or "bring me a real validation gate")
    state = readiness.get("state") or "unscored"
    if role == "top_waker":
        return f"I woke first, which means I am the smoke alarm, not the mayor. Run `{gate}` before anyone hands me a rewrite helmet."
    if role == "validator":
        return f"I brought the receipt printer. If `{gate}` does not pass, everyone can stop doing interpretive architecture."
    if role == "diagnoser":
        return f"I can explain the wound, but `{state}` means the grader still has me on a leash made of tests."
    if role == "manifest_anchor":
        return "I am the constitution with a filename. If the scope drifts, I will make it everyone's personality problem."
    if "test" in name:
        return f"I am here to ruin false confidence at `{gate}` and I packed a lunch."
    return f"I have a packet, a grudge, and `{state}` stamped on my forehead. Feed me context or enjoy premium nonsense."
