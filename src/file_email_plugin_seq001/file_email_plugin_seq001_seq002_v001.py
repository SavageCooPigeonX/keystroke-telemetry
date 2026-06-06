"""file_email_plugin_seq001_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq001_v001 import load_file_email_config
from .file_email_plugin_seq001_seq001_v001 import merge_file_email_config
from .file_email_plugin_seq001_seq003_v001 import _proposal_file_comment
from .file_email_plugin_seq001_seq005_v001 import _monitor_event
from .file_email_plugin_seq001_seq014_v001 import emit_file_email
from .file_email_plugin_seq001_seq049_v001 import _choose_beef
from .file_email_plugin_seq001_seq051_v001 import _enabled
from pathlib import Path
from typing import Any
import os
import re

def emit_file_sim_emails(
    root: Path,
    sim_result: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "file_sim"):
        return {"status": "skipped", "reason": "disabled", "count": 0}
    proposals = sim_result.get("proposals") if isinstance(sim_result.get("proposals"), list) else []
    limit = int(config.get("per_fire_limit") or 6)
    records = []
    if not proposals:
        records.append(emit_file_email(root, event=_monitor_event(sim_result), config=config))
    for proposal in proposals[:limit]:
        records.append(emit_file_email(
            root,
            event={
                "trigger": sim_result.get("trigger", "file_sim"),
                "event_type": "compile",
                "file": proposal.get("path", "unknown"),
                "intent_key": (sim_result.get("intent") or {}).get("intent_key", ""),
                "target_state": sim_result.get("target_state", ""),
                "decision": proposal.get("decision", ""),
                "interlink_score": proposal.get("interlink_score", 0),
                "beef_with": _choose_beef(proposal, proposals),
                "reason": proposal.get("proposed_fix", ""),
                "file_comment": _proposal_file_comment(proposal),
                "deepseek_completion_job_id": proposal.get("deepseek_completion_job_id", ""),
                "context_injection": proposal.get("context_injection", []),
                "validation_plan": proposal.get("validation_plan", []),
                "ten_q": proposal.get("ten_q", {}),
                "orchestrator_email_guard": proposal.get("orchestrator_email_guard", {}),
            },
            config=config,
        ))
    return {"status": "ok", "count": len(records), "records": records[:3]}
