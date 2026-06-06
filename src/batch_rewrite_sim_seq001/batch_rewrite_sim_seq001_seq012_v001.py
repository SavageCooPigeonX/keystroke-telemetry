"""batch_rewrite_sim_seq001_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _render_file_job_council(council: dict[str, Any]) -> str:
    lines = [
        "# File Job Council",
        "",
        f"- intent_key: `{council.get('intent_key', '')}`",
        f"- total_estimated_tokens: `{council.get('total_estimated_tokens', 0)}`",
        f"- total_proposals: `{council.get('total_proposals', 0)}`",
        "",
        council.get("comedy_summary", ""),
        "",
        "## Jobs",
        "",
    ]
    for job in council.get("jobs", []):
        lines.extend([
            f"### {job.get('job_id')} - {job.get('scope')}",
            "",
            f"- status: `{job.get('status')}`",
            f"- captain: `{job.get('captain')}`",
            f"- tokens: `{job.get('total_estimated_tokens')}`",
            f"- files: `{', '.join(job.get('files', []))}`",
            f"- context_files: `{', '.join(job.get('context_files', [])[:12])}`",
            f"- why: {job.get('why')}",
            "",
        ])
    lines.extend(["## Context Packs", ""])
    for pack in council.get("context_packs", []):
        lines.append(
            f"- `{pack.get('pack_id')}` ({pack.get('total_estimated_tokens')}/{pack.get('token_budget')} tokens, "
            f"skipped {len(pack.get('skipped_files') or [])}): "
            f"{', '.join(pack.get('files', []))}"
        )
    lines.extend(["", "## Roster", ""])
    for member in council.get("roster", [])[:20]:
        lines.append(
            f"- `{member.get('file')}` as `{member.get('role')}` "
            f"({member.get('approx_tokens')} tokens): {member.get('mood')} "
            f"Model grievance: {member.get('model_grievance')}"
        )
    lines.extend(["", "## Relationships", ""])
    for edge in council.get("relationships", [])[:40]:
        lines.append(f"- `{edge.get('from')}` {edge.get('type')} `{edge.get('to')}` - {edge.get('reason')}")
    lines.append("")
    return "\n".join(lines)
