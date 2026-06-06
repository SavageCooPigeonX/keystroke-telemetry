"""batch_rewrite_sim_seq001_seq020_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _check(key: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "reason": pass_reason if passed else fail_reason}


def _ten_q_failure_reason(score: int, min_score: int, missing: list[str]) -> str:
    parts = []
    if score < min_score:
        parts.append(f"score {score}/{min_score}")
    if missing:
        parts.append("missing required " + ", ".join(missing))
    return "; ".join(parts) or "failed consensus"


def _orchestrator_email_guard(
    proposal: dict[str, Any],
    ten_q: dict[str, Any],
    guard: dict[str, Any],
) -> dict[str, Any]:
    aligned = bool(ten_q.get("passed"))
    decision = "allow_email" if aligned else "local_only"
    if str(guard.get("email_send_policy") or "") == "block_all_when_failed" and not aligned:
        decision = "block_email"
    return {
        "schema": "orchestrator_email_guard/v1",
        "aligned": aligned,
        "decision": decision,
        "policy": guard.get("email_send_policy", "block_resend_when_failed"),
        "reason": "10Q consensus passed" if aligned else f"10Q consensus failed: {ten_q.get('reason')}",
    }


def _context_edges(proposal: dict[str, Any]) -> set[str]:
    edges = {str(proposal.get("path") or "")}
    edges.update(str(item) for item in (proposal.get("context_injection") or []) if item)
    validation = proposal.get("cross_file_validation") or {}
    edges.update(str(item) for item in (validation.get("referenced_by") or []) if item)
    return {edge.replace("\\", "/") for edge in edges if edge and not edge.lower().endswith("manifest.md")}


def _dedupe_incompatibilities(reports: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    out = []
    for report in reports:
        key = (report.get("with"), report.get("reason"))
        if key in seen:
            continue
        seen.add(key)
        out.append(report)
    return out[:4]
