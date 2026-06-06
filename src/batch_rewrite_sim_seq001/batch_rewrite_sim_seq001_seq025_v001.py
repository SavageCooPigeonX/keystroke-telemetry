"""batch_rewrite_sim_seq001_seq025_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq021_v001 import _render_email_guard
from .batch_rewrite_sim_seq001_seq021_v001 import _render_incompatibilities
from .batch_rewrite_sim_seq001_seq021_v001 import _render_ten_q
from typing import Any
import os
import re

def _render_file_push_narrative_fragment(result: dict[str, Any]) -> str:
    council = result.get("file_job_council") or {}
    lines = [
        "## File Comedy Dispatch",
        "",
        f"Intent `{(result.get('intent') or {}).get('intent_key', '')}` ran the file-sim court.",
        "Files wrote local mail, filed beef, and queued DeepSeek completion jobs for approved source rewrite paths.",
        "",
    ]
    if council:
        lines.extend([
            f"Council summary: {council.get('comedy_summary', '')}",
            "",
        ])
        for job in (council.get("jobs") or [])[:4]:
            lines.append(
                f"- `{job.get('job_id')}` packs `{job.get('total_estimated_tokens')}` tokens "
                f"around captain `{job.get('captain')}`; status `{job.get('status')}`"
            )
        lines.append("")
    for proposal in (result.get("proposals") or [])[:6]:
        lines.append(
            f"- `{proposal.get('path')}` wants `{proposal.get('overwrite_path')}` "
            f"after `{proposal.get('approval_gate')}`; 10Q {_render_ten_q(proposal)}; "
            f"guard {_render_email_guard(proposal)}; beef/conflicts: {_render_incompatibilities(proposal)}"
        )
    lines.extend([
        "",
        "Oath: Copilot executes the approved sim. DeepSeek drafts the deep path. Validation gets the veto.",
        "",
    ])
    return "\n".join(lines)
