"""Markdown renderers for file collaboration state."""
from __future__ import annotations

from typing import Any

from src.file_collaboration_metrics_seq001_v001 import improvement_notes


def render_file_collaboration_audit(result: dict[str, Any]) -> str:
    metrics = result.get("metrics") or {}
    lines = [
        "# File Collaboration Audit",
        "",
        result.get("operator_read", ""),
        "",
        "```text",
        f"verdict: {result.get('verdict')}",
        f"collaboration_score: {result.get('collaboration_score')}",
        f"relationship_edges: {metrics.get('relationship_edges', 0)}",
        f"learning_packets: {metrics.get('learning_packets', 0)}",
        f"peer_ready_packets: {metrics.get('peer_ready_packets', 0)}",
        f"outcome_pass_rate: {metrics.get('outcome_pass_rate', 0)}",
        f"edge_trend: {metrics.get('edge_trend', 'unknown')}",
        "```",
        "",
        "## What Improved",
        "",
    ]
    for item in improvement_notes(metrics):
        lines.append(f"- {item}")
    lines.extend(["", "## What Is Still Fake", ""])
    for item in result.get("missing_loops") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Manifest Collaboration State", ""])
    state = result.get("manifest_state") or {}
    for room in state.get("rooms", [])[:3]:
        lines.append(f"### {room.get('room_id')}")
        lines.append(f"- shared goal: {room.get('shared_goal')}")
        lines.append(f"- files: {', '.join(f'`{item}`' for item in room.get('files', [])[:8])}")
        lines.append(f"- agreement: {room.get('agreement')}")
        if room.get("open_objections"):
            lines.append(f"- objections: {'; '.join(room.get('open_objections')[:4])}")
        lines.append("")
        for comment in room.get("comments", [])[:6]:
            lines.append(f"- `{comment.get('from_file')}` -> {comment.get('quote')}")
        lines.append("")
    lines.extend(["## Next Moves", ""])
    for item in result.get("recommended_next_moves") or []:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def render_manifest_collaboration_state(state: dict[str, Any]) -> str:
    lines = [
        "# File Manifest Collaboration State",
        "",
        f"- generated_at: `{state.get('ts', '')}`",
        f"- primary_goal: `{state.get('primary_goal', '')}`",
        f"- routing_rule: {state.get('routing_rule', '')}",
        "",
    ]
    for room in state.get("rooms", []):
        lines.extend([
            f"## {room.get('room_id')}",
            "",
            f"- intent_key: `{room.get('intent_key', '')}`",
            f"- shared_goal: {room.get('shared_goal', '')}",
            f"- agreement: {room.get('agreement', '')}",
            f"- next_plan: {room.get('next_plan', '')}",
            "",
            "### File Comments",
            "",
        ])
        for comment in room.get("comments", []):
            to_files = ", ".join(f"`{item}`" for item in comment.get("to_files", [])[:6]) or "`manifest_state`"
            lines.append(f"- `{comment.get('from_file')}` to {to_files}: {comment.get('quote')}")
            lines.append(f"  - learned: {comment.get('learned')}")
            lines.append(f"  - plan: {comment.get('plan')}")
            if comment.get("blockers"):
                lines.append(f"  - blockers: {'; '.join(comment.get('blockers')[:4])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
