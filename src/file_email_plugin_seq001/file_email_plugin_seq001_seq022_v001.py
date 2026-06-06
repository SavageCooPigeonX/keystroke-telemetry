"""file_email_plugin_seq001_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq018_v001 import _learning_validation_plan
from pathlib import Path
from typing import Any
import json
import os
import re

def _learning_story_cast(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[str]:
    packet_by_file = {
        str(packet.get("file")): packet
        for packet in packets
        if isinstance(packet, dict) and packet.get("file")
    }
    lines = []
    for node in wake_order[:5]:
        file_path = str(node.get("file") or "unknown")
        packet = packet_by_file.get(file_path, {})
        validation = _learning_validation_plan([packet]) if packet else []
        role = node.get("role", "learner")
        next_q = node.get("next_question", "ask the grader what proof is missing")
        lines.append(
            f"- `{Path(file_path).name}` as `{role}`: wants `{validation[0] if validation else next_q}` before anyone touches source."
        )
    return lines or ["- No cast formed. The ranker owes you a better audition."]


def _learning_story_deepseek(
    packets: list[dict[str, Any]],
    context: list[str],
    validation: list[str],
) -> list[str]:
    if not packets:
        return ["- Nothing yet. DeepSeek gets no prompt until a file earns the stage."]
    top = packets[0]
    lines = [
        f"- File: `{top.get('file')}`",
        f"- Packet: `{top.get('packet_id')}`",
        f"- Load first: `{', '.join(context[:5]) or 'context still thin'}`",
        f"- Do not draft a full overwrite. Draft diagnosis, smallest patch hypothesis, risk, and the test it must survive.",
    ]
    if validation:
        lines.append(f"- First grader demand: `{validation[0]}`")
    return lines


def _learning_story_grader(validation: list[str]) -> list[str]:
    if not validation:
        return ["- No tests, no crown. The grader refuses to certify vibes."]
    return [
        f"- `{validation[0]}` passes.",
        "- A context pack exists and is not stale.",
        "- The file can explain what it learned after success or failure.",
        "- The backward-learning pass writes the reward into `file_profiles.json`.",
    ]
