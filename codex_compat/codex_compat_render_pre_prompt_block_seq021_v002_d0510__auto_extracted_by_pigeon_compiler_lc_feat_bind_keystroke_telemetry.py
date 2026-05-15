"""codex_compat_render_pre_prompt_block_seq021_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 021 | VER: v002 | 62 lines | ~647 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_parse_deleted_words_seq003_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _parse_deleted_words
from typing import Any
import os
import re

def _render_pre_prompt_block(state: dict[str, Any]) -> str:
    context = state.get("context_selection") or {}
    composition = state.get("composition") or {}
    sim = state.get("sim") or {}
    file_sim = state.get("file_sim") or {}
    files = context.get("files") or []
    deleted_words = _parse_deleted_words(composition.get("deleted_words") or [], composition.get("deleted_text", ""))

    lines = [
        "<!-- codex:pre-prompt-state -->",
        "## Codex Pre-Prompt State",
        "",
        f"*Prepared {state.get('ts', '')} before model handoff*",
        "",
        f"**PROMPT:** `{state.get('final_text', '')[:220]}`",
        "",
        f"**DELETION_RATIO:** `{composition.get('deletion_ratio', 0)}`",
        f"**DELETED_WORDS:** {', '.join(deleted_words[:12]) if deleted_words else 'none'}",
        f"**HESITATION_COUNT:** `{state.get('hesitation_count', 0)}`",
        "",
        "**NUMERIC_CONTEXT:**",
    ]
    if files:
        for file_ref in files[:8]:
            lines.append(f"- `{file_ref.get('name', '?')}` score={file_ref.get('score', 0)}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        f"**HANDOFF_READY:** `{state.get('handoff_ready', False)}`",
        f"**SIM_STATUS:** `{sim.get('status', 'not_run')}`",
        f"**FILE_SIM_STATUS:** `{file_sim.get('status', 'not_run')}`",
        f"**FILE_SIM_TARGET_STATE:** `{file_sim.get('target_state', 'none')}`",
    ])
    proposals = file_sim.get("proposals") or []
    if proposals:
        lines.append("**FILE_SIM_SOURCE_REWRITES:**")
        for proposal in proposals[:5]:
            lines.append(
                f"- `{proposal.get('path')}` interlink={proposal.get('interlink_score')} "
                f"decision={proposal.get('decision')}"
            )
    if state.get("block_reason"):
        lines.append(f"**BLOCK_REASON:** {state['block_reason']}")
    sim_tail = (sim.get("stdout") or "").strip().splitlines()[-8:]
    if sim_tail:
        lines.append("**SIM_OUTPUT:**")
        lines.extend(f"- {line[:180]}" for line in sim_tail)

    unsaid = composition.get("unsaid_reconstruction")
    if unsaid:
        lines.extend(["", f"**UNSAID_RECONSTRUCTION:** {unsaid[:400]}"])

    lines.append("<!-- /codex:pre-prompt-state -->")
    return "\n".join(lines)
