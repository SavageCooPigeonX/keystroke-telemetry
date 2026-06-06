"""file_self_sim_learning_seq001_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _backward_learning_plan(packets: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "armed_waiting_for_outcome",
        "record_function": "record_file_learning_outcome(root, packet_id, outcome, reward, details)",
        "on_success": [
            "increase selected file intent/profile affinity",
            "strengthen context vein edges that were loaded",
            "mark validation packet as trusted for similar future intent",
        ],
        "on_failure": [
            "lower selected file affinity for this intent cluster",
            "record missing context or incompatible peer",
            "wake validator earlier in the next sequence",
        ],
        "packet_ids": [packet.get("packet_id") for packet in packets],
    }
