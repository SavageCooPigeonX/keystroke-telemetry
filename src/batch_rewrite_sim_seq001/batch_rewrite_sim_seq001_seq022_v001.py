"""batch_rewrite_sim_seq001_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq023_v001 import _deepseek_completion_prompt
from .batch_rewrite_sim_seq001_seq023_v001 import _deepseek_model
from typing import Any
import hashlib
import json
import os
import re

def _deepseek_completion_job(result: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    file_path = str(proposal.get("path") or "unknown")
    intent = result.get("intent") or {}
    seed = json.dumps({
        "ts": result.get("ts"),
        "intent_key": intent.get("intent_key"),
        "file": file_path,
        "reason": proposal.get("proposed_fix"),
    }, sort_keys=True, ensure_ascii=False)
    job_id = "dsc-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return {
        "schema": "deepseek_code_completion/v1",
        "ts": result.get("ts"),
        "job_id": job_id,
        "status": "queued_for_orchestrator_approval",
        "model": _deepseek_model(),
        "mode": "source_rewrite_completion",
        "file": file_path,
        "intent_key": intent.get("intent_key", ""),
        "target_state": result.get("target_state", "interlinked_source_state"),
        "reasoning_budget": (proposal.get("reasoning_budget") or {}).get("deep_rewrite", "full_after_approval"),
        "copilot_role": "sim_executor",
        "prompt": _deepseek_completion_prompt(result, proposal),
        "context_injection": proposal.get("context_injection", []),
        "validation_plan": proposal.get("validation_plan", []),
        "incompatibilities": proposal.get("incompatibilities", []),
        "ten_q": proposal.get("ten_q", {}),
        "orchestrator_email_guard": proposal.get("orchestrator_email_guard", {}),
        "approval_gate": proposal.get("approval_gate", "operator_required"),
        "autonomous_write": False,
    }
