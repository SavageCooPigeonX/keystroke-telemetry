"""batch_rewrite_sim_seq001_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq021_v001 import _render_email_guard
from .batch_rewrite_sim_seq001_seq021_v001 import _render_incompatibilities
from .batch_rewrite_sim_seq001_seq021_v001 import _render_ten_q
from typing import Any
import os
import re

def render_batch_rewrite_sim(result: dict[str, Any]) -> str:
    intent = result.get("intent", {})
    lines = [
        "# Batch Rewrite Sim",
        "",
        "Source rewrite orchestration lane. It compiles intent, proposes fixes, waits for approval,",
        "injects extra context, explains incompatible layouts, then reserves deep rewrite tokens for approved overwrites.",
        "",
        "```text",
        f"intent_key: {intent.get('intent_key', '')}",
        f"mode: {result.get('mode')}",
        f"target_state: {result.get('target_state')}",
        f"auto_write_allowed: {result.get('orchestrator', {}).get('auto_write_allowed')}",
        "```",
        "",
        "## Rewrite Ladder",
        "",
    ]
    ladder = result.get("rewrite_orchestration") or {}
    for stage in ladder.get("stages", []):
        lines.append(f"- `{stage.get('name')}` via `{stage.get('engine')}` - {stage.get('budget')}")
    lines.extend([
        "",
        "## Dead Token Collective Hearing",
        "",
        "The old filenames testify. Source files get rewritten toward interlinked state.",
        "",
    ])
    for i, prop in enumerate(result.get("proposals", [])[:10], 1):
        lines.extend([
            f"### Q{i} - {prop.get('path')}",
            "",
            f"- decision: `{prop.get('decision')}`",
            f"- reward: `{prop.get('reward')}` risk: `{prop.get('risk')}` confidence: `{prop.get('confidence')}`",
            f"- proposed_fix: {prop.get('proposed_fix')}",
            f"- approval_gate: `{prop.get('approval_gate')}`",
            f"- overwrite_path: `{prop.get('overwrite_path')}`",
            f"- context_injection: `{', '.join(prop.get('context_injection', [])[:5]) or 'none'}`",
            f"- validation: `{', '.join(prop.get('validation_plan', [])[:4]) or 'none'}`",
            f"- incompatibilities: `{_render_incompatibilities(prop)}`",
            f"- 10Q consensus: `{_render_ten_q(prop)}`",
            f"- email_guard: `{_render_email_guard(prop)}`",
            "",
        ])
    council = result.get("file_job_council") or {}
    if council:
        lines.extend([
            "## File Job Council",
            "",
            council.get("comedy_summary", "Files organized themselves into context packs."),
            "",
        ])
        for job in (council.get("jobs") or [])[:6]:
            lines.extend([
                f"### {job.get('job_id')} - {job.get('scope')}",
                "",
                f"- captain: `{job.get('captain')}`",
                f"- status: `{job.get('status')}`",
                f"- total_estimated_tokens: `{job.get('total_estimated_tokens')}`",
                f"- files: `{', '.join(job.get('files', [])[:6]) or 'none'}`",
                f"- why: {job.get('why')}",
                "",
            ])
        lines.extend(["### Context Packs", ""])
        for pack in (council.get("context_packs") or [])[:6]:
            lines.append(
                f"- `{pack.get('pack_id')}` {pack.get('purpose')} "
                f"({pack.get('total_estimated_tokens')}/{pack.get('token_budget')} tokens, "
                f"skipped {len(pack.get('skipped_files') or [])}): "
                f"`{', '.join(pack.get('files', [])[:8]) or 'none'}`"
            )
        lines.extend(["", "### Relationships", ""])
        for edge in (council.get("relationships") or [])[:8]:
            lines.append(
                f"- `{edge.get('from')}` {edge.get('type')} `{edge.get('to')}` - {edge.get('reason')}"
            )
        lines.append("")
    lines.extend([
        "## Final Rule",
        "",
        "The simulator can propose. File emails testify. DeepSeek drafts only after approval. Copilot executes and validates.",
        "",
        "## Orchestrator Oath",
        "",
        result.get("orchestrator_oath", {}).get("short", "No oath recorded."),
        "",
    ])
    return "\n".join(lines)
