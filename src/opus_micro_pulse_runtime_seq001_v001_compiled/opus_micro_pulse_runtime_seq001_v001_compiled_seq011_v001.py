"""opus_micro_pulse_runtime_seq001_v001_compiled_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import json
import re

def _render_executor_prompt(
    *,
    prompt: str,
    classification: dict[str, Any],
    session: dict[str, Any],
    predicted: list[str],
    selected_manifests: list[str],
    interrogations: list[dict[str, Any]],
    quick_fixes: list[str],
    stale: list[dict[str, Any]],
    theories: list[dict[str, Any]],
) -> str:
    lines = [
        "# Opus Executor Prompt",
        "",
        "This generated prompt is the primary instruction packet for Codex/Copilot.",
        "Use the raw operator prompt only as fallback evidence when this packet is ambiguous.",
        "",
        "## Execution Gate",
        "",
        f"- prompt_class: `{classification['prompt_class']}`",
        f"- sim_policy: `{classification['sim_policy']}`",
        f"- executor_session: `{session['executor_session']}`",
        f"- executor_reason: {session['reason']}",
        "",
        "## Operator Fallback Prompt",
        "",
        prompt,
        "",
        "## Required Read Set",
        "",
        "- `logs/prompt_cannon_job_latest.json`",
        "- `logs/opus_micro_pulse_latest.json`",
        "- `logs/cannon_execution_gate_latest.json`",
        "- `MANIFEST.md`",
        "- `ROOT_SIM_KEYS.md`",
    ]
    for rel in selected_manifests:
        lines.append(f"- `{rel}`")
    lines.extend(["", "## Predicted File Chain", ""])
    lines.extend(f"- `{rel}`" for rel in predicted)
    lines.extend(["", "## Quick Fix / Improvement Queue", ""])
    if quick_fixes:
        lines.extend(f"- {row}" for row in quick_fixes[:12])
    else:
        lines.append("- `none-surfaced`")
    lines.extend(["", "## File Intelligence", ""])
    for row in interrogations[:18]:
        lines.extend([
            f"### {row.get('file')}",
            "",
            f"- opus_reason: {row.get('opus_reason')}",
            f"- self_model: {row.get('file_self_model')}",
            f"- file_comment: {row.get('file_comment')}",
            f"- coding_agent: {row.get('coding_agent_note')}",
            f"- deepseek_folder_manager: {row.get('deepseek_folder_manager_note')}",
            "",
        ])
    if not interrogations:
        lines.append("- `none-selected`")
    lines.extend(["", "## Stale / Blocking Evidence", ""])
    if stale:
        for row in stale[:12]:
            lines.append(f"- `{row.get('severity')}` `{row.get('owner')}` {row.get('title')} :: {row.get('next_action')}")
    else:
        lines.append("- `none-surfaced`")
    lines.extend(["", "## Opus Theories", ""])
    for row in theories[:9]:
        lines.append(f"- `{row.get('theory')}` confidence={row.get('confidence')} :: {row.get('reason')}")
    lines.extend([
        "",
        "## Executor Contract",
        "",
        "- Do not execute from the raw operator prompt alone.",
        "- Treat this packet as the refined task.",
        "- Complete local quick fixes when they are inside the selected file chain.",
        "- If a quick fix is not local, defer it explicitly in the closeout receipt.",
        "- After work, write a touched-file receipt for backward file-intelligence learning.",
    ])
    return "\n".join(lines) + "\n"
