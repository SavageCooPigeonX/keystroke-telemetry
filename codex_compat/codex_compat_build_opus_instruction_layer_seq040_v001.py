"""codex_compat_build_opus_instruction_layer_seq040_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _build_opus_instruction_layer(
    prompt: str,
    focus_files: list[dict[str, Any]],
    context_selection: dict[str, Any],
    signals: dict[str, Any],
) -> dict[str, Any]:
    """Build the operator-facing instruction layer that Opus manages.

    This layer is intentionally deterministic: Opus can interpret the selected
    files and operator state from it, and Codex/Copilot can leave response
    residue without needing another model call.
    """
    selected_files: list[dict[str, Any]] = []
    for item in focus_files[:12]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        selected_files.append({
            "file": name,
            "reason": str(item.get("reason") or "context"),
            "score": item.get("score"),
            "residue_comment": (
                f"{name}: selected via {item.get('reason') or 'context'} for this prompt; "
                "preserve useful findings in the response file comments."
            ),
        })

    return {
        "schema": "opus_instruction_layer/v1",
        "status": "active",
        "fires_for_prompt": bool(str(prompt or "").strip()),
        "manager": "opus",
        "role": "file interpreter and operator hands for Codex instruction routing",
        "self_improving_source": "selected-file comments, dynamic context packs, prompt telemetry, and file self-knowledge logs",
        "prompt_format": {
            "first_read": "Start from this Opus layer, then reconcile pre-prompt state and dynamic context.",
            "selected_file_policy": "Treat selected files as the editable/inspectable working set unless the prompt clearly overrides them.",
            "operator_policy": "Use the operator response policy when present; otherwise stay direct, concrete, and implementation-first.",
        },
        "response_contract": {
            "file_comments_required": True,
            "section_name": "File Comments",
            "format": "`path`: one short residue note about why it was selected, what changed or was learned, and what remains risky.",
            "minimum": "Include one comment for each selected or touched file when any selected files exist.",
            "purpose": "Leave compact residue context that future Copilot/Codex turns can reuse.",
        },
        "selected_files": selected_files,
        "context_confidence": context_selection.get("confidence", 0),
        "cognitive_state": signals.get("cognitive_state") or "unknown",
    }
