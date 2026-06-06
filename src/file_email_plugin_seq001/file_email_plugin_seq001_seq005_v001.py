"""file_email_plugin_seq001_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import json
import os
import re

def _monitor_event(sim_result: dict[str, Any]) -> dict[str, Any]:
    intent_key = (sim_result.get("intent") or {}).get("intent_key", "")
    ten_q = {
        "schema": "file_consensus_10q/v1",
        "score": 4,
        "max_score": 10,
        "min_score": 7,
        "passed": False,
        "reason": "no source file proposals were selected",
        "checks": [
            {"key": "intent_alignment", "passed": bool(intent_key), "reason": "intent compiled" if intent_key else "intent did not compile"},
            {"key": "source_target", "passed": False, "reason": "no source target selected"},
            {"key": "context_available", "passed": bool((sim_result.get("distributed_intent_encoding") or {}).get("file_votes")), "reason": "numeric context inspected"},
            {"key": "validation_plan", "passed": False, "reason": "no file-specific validation plan"},
            {"key": "operator_approval", "passed": True, "reason": "operator approval is required"},
            {"key": "deepseek_job_allowed", "passed": False, "reason": "DeepSeek job blocked without file target"},
            {"key": "incompatibility_known", "passed": True, "reason": "no peer proposals to conflict"},
            {"key": "identity_growth", "passed": False, "reason": "no file identity grew"},
            {"key": "dirty_state_known", "passed": True, "reason": "sim self model inspected dirty files"},
            {"key": "file_exists", "passed": False, "reason": "no file target exists"},
        ],
    }
    return {
        "trigger": sim_result.get("trigger", "file_sim"),
        "event_type": "compile",
        "file": "orchestrator/prompt_monitor",
        "intent_key": intent_key,
        "target_state": sim_result.get("target_state", "interlinked_source_state"),
        "decision": "no_file_proposals",
        "interlink_score": 0,
        "beef_with": "candidate_ranker",
        "reason": "prompt fired through orchestrator, but no source files were selected; request more context before rewrite",
        "deepseek_completion_job_id": "blocked_by_no_file_candidates",
        "context_injection": ["logs/batch_rewrite_sim_latest.json", "logs/dynamic_context_pack.json"],
        "validation_plan": ["review prompt intent", "add manifest/context target", "rerun file sim"],
        "ten_q": ten_q,
        "orchestrator_email_guard": {
            "schema": "orchestrator_email_guard/v1",
            "aligned": False,
            "decision": "local_only",
            "policy": "block_resend_when_failed",
            "reason": "10Q consensus failed: no source file proposals were selected",
        },
    }
