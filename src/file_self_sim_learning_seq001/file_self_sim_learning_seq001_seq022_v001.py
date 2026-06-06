"""file_self_sim_learning_seq001_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _render_learning_markdown(result: dict[str, Any]) -> str:
    intent = result.get("intent") or {}
    lines = [
        "# File Self-Sim Learning Mode",
        "",
        "This is not a notification lane. It is the learning-only substrate for approval-gated self-overwrite.",
        "",
        "```text",
        f"intent_key: {intent.get('intent_key', '')}",
        f"mode: {result.get('mode')}",
        f"target_state: {result.get('target_state')}",
        "source_overwrite: blocked until approval and validation",
        "```",
        "",
        "## Wake Order",
        "",
    ]
    for node in result.get("wake_order", [])[:12]:
        lines.append(
            f"{node.get('sequence')}. `{node.get('file')}` - {node.get('role')} "
            f"(score {node.get('wake_score')})"
        )
        lines.append(f"   - why: {node.get('wake_reason') or 'selected by profile signals'}")
        size = node.get("size_pressure") or {}
        if size.get("needs_split_plan"):
            lines.append(
                f"   - split pressure: {size.get('state')} "
                f"({size.get('line_count')} lines, pressure {size.get('pressure')})"
            )
        lines.append(
            f"   - relationship/validation: {node.get('relationship_weight', 0)} / "
            f"{node.get('validation_confidence', 0)}"
        )
        lines.append(f"   - next: {node.get('next_question')}")
    lines.extend(["", "## Diagnosis Flow", ""])
    for step in result.get("diagnosis_flow", []):
        lines.append(f"- `{step.get('stage')}` by `{step.get('owner')}`: {step.get('action')}")
    lines.extend(["", "## Learning Packets", ""])
    for packet in result.get("learning_packets", [])[:10]:
        readiness = packet.get("overwrite_readiness") or {}
        lines.append(f"### {packet.get('file')}")
        lines.append(f"- packet: `{packet.get('packet_id')}`")
        lines.append(f"- readiness: `{readiness.get('state')}` - {readiness.get('reason')}")
        lines.append(
            "- context veins: "
            + (", ".join(f"`{item.get('file')}`" for item in packet.get("context_veins", [])[:6]) or "none")
        )
        lines.append(
            "- validation: "
            + (", ".join(f"`{item}`" for item in (packet.get("verification_packet") or {}).get("validation_plan", [])[:4]) or "none")
        )
        lines.append("")
    registry = result.get("architecture_sequence_registry") or {}
    summary = registry.get("summary") or {}
    lines.extend(["## Architecture Sequence Registry", ""])
    lines.append(
        f"- files: `{summary.get('files', 0)}` ok `{summary.get('ok', 0)}` "
        f"over_soft `{summary.get('over_soft', 0)}` warn `{summary.get('warn', 0)}` "
        f"critical `{summary.get('critical', 0)}`"
    )
    lines.append("- policy: filename seq stays local; registry `arch_seq` is the global program spine")
    graph = result.get("relationship_graph") or {}
    lines.extend(["", "## Relationship Graph", ""])
    lines.append(f"- nodes: `{len(graph.get('nodes') or [])}` edges: `{len(graph.get('edges') or [])}`")
    for edge in (graph.get("edges") or [])[:6]:
        lines.append(
            f"- `{edge.get('from')}` <-> `{edge.get('to')}` "
            f"{edge.get('relation')} weight `{edge.get('weight')}`"
        )
    split_jobs = result.get("overcap_split_jobs") or []
    lines.extend(["", "## Over-Cap Split Jobs", ""])
    if split_jobs:
        for job in split_jobs[:8]:
            lines.append(
                f"- `{job.get('file')}` {job.get('size_state')} "
                f"{job.get('line_count')} lines -> `{job.get('status')}`"
            )
            lines.append(f"  - {job.get('file_quote')}")
    else:
        lines.append("- none")
    plan = result.get("interlink_plan") or {}
    lines.extend(["## Interlink Plan", ""])
    for job in plan.get("near_term_jobs", []):
        lines.append(f"- `{job.get('job')}`: {job.get('action')} ({len(job.get('files') or [])} file(s))")
    lines.extend(["", "## Backward Learning Pass", ""])
    back = result.get("backward_learning_pass") or {}
    lines.append(f"- status: `{back.get('status')}`")
    lines.append(f"- record: `{back.get('record_function')}`")
    return "\n".join(lines) + "\n"
