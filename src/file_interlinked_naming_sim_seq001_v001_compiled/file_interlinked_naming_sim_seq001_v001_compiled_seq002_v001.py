"""file_interlinked_naming_sim_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import _email_reason
from pathlib import Path
from src.file_interlinked_naming_policy_seq001_v001 import (
    corrected_intent,
    discrepancy,
    file_kind,
    interlinked_queries,
    proposed_name,
    standard,
)
from typing import Any
import re

def send_naming_grader_email(root: Path, sim: dict[str, Any]) -> dict[str, Any]:
    """Send the naming plan through the file-room text-chain renderer."""
    from src.file_email_plugin_seq001_v001 import emit_file_email, load_file_email_config

    participants = sim.get("participants") or []
    standard = sim.get("standard_vote") or {}
    event = {
        "trigger": "file_sim",
        "event_type": "compile",
        "file": "orchestrator/interlinked_naming_grader",
        "intent_key": "root:plan:interlinked_naming_standard:major",
        "target_state": "interlinked_files_agree_before_rename",
        "decision": "plan_only",
        "reason": _email_reason(participants, standard),
        "file_comment": "Correction: downgrade flattening; files get F keys, display names, symbolic identity, and last_change mutation state.",
        "context_injection": [row["file"] for row in participants[:8]],
        "validation_plan": ["py -m pytest test_file_interlinked_naming_sim.py -q", "git diff --check"],
        "ten_q": {"passed": True, "score": 10, "max_score": 10, "reason": "planning gate passed"},
        "orchestrator_email_guard": {"decision": "allow_email", "aligned": True},
    }
    return emit_file_email(root, event, config=load_file_email_config(root) | {"delivery_mode": "resend_dry_run"})


def render_interlinked_naming_sim(sim: dict[str, Any]) -> str:
    lines = ["# Interlinked Naming Sim", "", f"- task: {sim.get('task')}", f"- decision: `{(sim.get('grader_gate') or {}).get('decision')}`", "", "## Standard Vote"]
    standard = sim.get("standard_vote") or {}
    lines.append(f"- convention: `{standard.get('convention')}`")
    lines.append(f"- rationale: {standard.get('rationale')}")
    lines.append(f"- correction: `{(sim.get('correction') or {}).get('downgrade')}`")
    lines.extend(["", "## File Query Answers"])
    for row in sim.get("participants") or []:
        ident = row.get("identity") or {}
        lines.append(f"- `{ident.get('number_key')}` {ident.get('operator_display_name')}: `{row['file']}` -> `{row['proposed_name']}` | {row['discrepancy']}")
    return "\n".join(lines) + "\n"
