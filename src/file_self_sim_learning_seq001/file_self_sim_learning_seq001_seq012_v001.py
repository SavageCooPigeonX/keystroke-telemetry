"""file_self_sim_learning_seq001_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _diagnosis_flow(wake_order: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not wake_order:
        return []
    top = wake_order[0]["file"]
    return [
        {
            "stage": "wake",
            "owner": top,
            "action": "select top file by numeric intent, history, memory, and profile signals",
        },
        {
            "stage": "load_identity",
            "owner": top,
            "action": "load file profile, mail memory, prior sim outcomes, manifest, and tests",
        },
        {
            "stage": "sequence_peers",
            "owner": "orchestrator",
            "action": "order peer files by context veins before rewrite planning",
            "files": [item["file"] for item in wake_order],
        },
        {
            "stage": "diagnose",
            "owner": "file_council",
            "action": "each file states responsibility, missing context, and validation gate",
        },
        {
            "stage": "emit_packets",
            "owner": "deepseek_learning_queue",
            "action": "write draft-only learning packets for deep rewrite reasoning",
        },
        {
            "stage": "approval_gate",
            "owner": "operator",
            "action": "no source overwrite until approval plus compile/test gate exists",
        },
        {
            "stage": "backward_learning",
            "owner": "file_profiles",
            "action": "record reward, failure reason, and sibling effects after execution",
        },
    ]
