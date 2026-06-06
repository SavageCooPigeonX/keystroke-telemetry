"""file_email_plugin_seq001_seq018_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq040_v001 import _dedupe_list
from typing import Any
import re

def _learning_interlink_score(learning_result: dict[str, Any]) -> float:
    wake_order = learning_result.get("wake_order") if isinstance(learning_result.get("wake_order"), list) else []
    if not wake_order:
        return 0.0
    scores = [float(item.get("wake_score") or 0) for item in wake_order if isinstance(item, dict)]
    return round(min(1.0, sum(scores[:6]) / max(1.0, len(scores[:6]) * 12.0)), 3)


def _learning_packet_summary(packets: list[dict[str, Any]]) -> str:
    ids = [str(packet.get("packet_id")) for packet in packets if isinstance(packet, dict) and packet.get("packet_id")]
    if not ids:
        return "no_packets"
    return f"{len(ids)} packet(s): " + ", ".join(ids[:4])


def _learning_context_files(learning_result: dict[str, Any]) -> list[str]:
    out = []
    plan = learning_result.get("interlink_plan") if isinstance(learning_result.get("interlink_plan"), dict) else {}
    for job in plan.get("near_term_jobs") or []:
        if isinstance(job, dict):
            out.extend(str(item) for item in job.get("files") or [])
    for node in learning_result.get("wake_order") or []:
        if isinstance(node, dict):
            out.append(str(node.get("file") or ""))
            out.extend(str(item.get("file") or "") for item in node.get("context_veins") or [] if isinstance(item, dict))
    return [item for item in _dedupe_list([item for item in out if item])[:16]]


def _learning_validation_plan(packets: list[dict[str, Any]]) -> list[str]:
    out = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        verification = packet.get("verification_packet") if isinstance(packet.get("verification_packet"), dict) else {}
        out.extend(str(item) for item in verification.get("validation_plan") or [])
    return _dedupe_list([item for item in out if item])[:8]
