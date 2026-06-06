"""batch_rewrite_sim_seq001_seq019_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq020_v001 import _check
from .batch_rewrite_sim_seq001_seq033_v001 import _tokens
from typing import Any
import os
import re

def _ten_q_checks(proposal: dict[str, Any], compiled: dict[str, Any]) -> list[dict[str, Any]]:
    validation = proposal.get("cross_file_validation") or {}
    identity = proposal.get("identity_growth") or {}
    context = proposal.get("context_injection") or []
    validation_plan = proposal.get("validation_plan") or []
    prompt_tokens = set(compiled.get("tokens") or [])
    file_tokens = _tokens(" ".join([
        str(proposal.get("path") or ""),
        str(proposal.get("proposed_fix") or ""),
        " ".join(str(item) for item in proposal.get("evidence") or []),
    ]))
    return [
        _check(
            "intent_alignment",
            bool(prompt_tokens and (prompt_tokens & file_tokens)) or bool(proposal.get("evidence")),
            "prompt/file/history tokens intersect",
            "no prompt or history signal explains this file",
        ),
        _check(
            "source_target",
            proposal.get("rewrite_target_type") == "source",
            "target is source code",
            "target is context or metadata only",
        ),
        _check(
            "context_available",
            bool(context),
            "context pack is present",
            "no context files selected",
        ),
        _check(
            "validation_plan",
            bool(validation_plan) and not str(validation_plan[0]).startswith("hold:"),
            "compile/test gate exists",
            "validation is missing or only hold",
        ),
        _check(
            "operator_approval",
            proposal.get("approval_gate") == "operator_required",
            "operator approval is required",
            "no operator approval gate",
        ),
        _check(
            "deepseek_job_allowed",
            proposal.get("overwrite_path") == "eligible_for_deepseek_after_approval",
            "deep rewrite path is eligible after approval",
            "deep rewrite path is blocked",
        ),
        _check(
            "incompatibility_known",
            isinstance(proposal.get("incompatibilities"), list),
            "peer incompatibility scan ran",
            "peer incompatibility scan missing",
        ),
        _check(
            "identity_growth",
            bool(identity) and float(identity.get("interlink_score") or 0) >= 0,
            "file identity growth record exists",
            "file identity growth was not computed",
        ),
        _check(
            "dirty_state_known",
            "dirty" in validation,
            "working tree state is known",
            "dirty state unknown",
        ),
        _check(
            "file_exists",
            bool(validation.get("exists")),
            "target file exists",
            "target file missing",
        ),
    ]
