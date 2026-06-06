"""batch_rewrite_sim_seq001_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from typing import Any
import os
import re

def _rewrite_orchestration(config: dict[str, Any]) -> dict[str, Any]:
    orch = config.get("rewrite_orchestration") if isinstance(config.get("rewrite_orchestration"), dict) else {}
    policy = orch.get("reasoning_policy") if isinstance(orch.get("reasoning_policy"), dict) else {}
    return {
        "principle": "do not spend deep rewrite tokens until a candidate survives proposal, grading, context injection, compatibility, and approval",
        "stages": [
            {
                "name": "proposal",
                "engine": orch.get("proposal_model", "gemini_quick"),
                "budget": policy.get("proposal", "low_latency"),
                "purpose": "cheap candidate generation from intent, history, and file identity",
            },
            {
                "name": "grader",
                "engine": orch.get("grader_model", "gemini_quick_grader"),
                "budget": policy.get("grader", "focused"),
                "purpose": "reject vague, stale, or low-interlink proposals",
            },
            {
                "name": "context_injection",
                "engine": orch.get("context_injector", "manifest_prompt_brain_context_pack"),
                "budget": "deterministic",
                "purpose": "assemble manifests, prompt brain, peer files, and validation plan",
            },
            {
                "name": "compatibility_referee",
                "engine": "local_cross_file_layout_check",
                "budget": "deterministic",
                "purpose": "tell files why competing proposals cannot both land",
            },
            {
                "name": "deep_rewrite_compile",
                "engine": orch.get("deep_rewrite_model", "deepseek_deep_path"),
                "budget": policy.get("overwrite", "deep_only_after_approval"),
                "purpose": "approved source overwrite followed by compile/test validation",
            },
        ],
    }


def _overwrite_path(decision: str, rel: str) -> str:
    if decision == "blocked":
        return "blocked_before_overwrite"
    if not _source_candidate(rel):
        return "context_only_no_overwrite"
    return "eligible_for_deepseek_after_approval"
