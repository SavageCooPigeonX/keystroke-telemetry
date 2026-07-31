"""file_interview_mode_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _load_jsonl
from pathlib import Path
from typing import Any
import json
import re

def _latest_push_cycle(root: Path) -> dict[str, Any]:
    rows = _load_jsonl(root / "logs" / "push_cycles.jsonl", limit=5)
    if not rows:
        return {}
    row = rows[-1]
    return {
        "commit": row.get("commit", ""),
        "cycle_number": row.get("cycle_number", 0),
        "sync_score": (row.get("sync") or {}).get("score"),
        "modules_touched": (row.get("copilot_signal") or {}).get("modules_touched", [])[:12],
        "coaching": row.get("coaching", {}),
    }


def _risk_for_file(rel: str, text: str, alias: dict[str, Any], questions: list[str]) -> dict[str, Any]:
    risks = []
    line_count = len(text.splitlines())
    if line_count > 200:
        risks.append("over_cap")
    if alias.get("status") == "no_alias_record":
        risks.append("identity_not_recorded")
    if questions:
        risks.append("pending_context_questions")
    if "_v001" in rel and "_d0510" not in rel:
        risks.append("possibly_stale_version")
    return {"level": "high" if "over_cap" in risks else ("medium" if risks else "low"), "items": risks}


def _proposed_fix(
    rel: str,
    questions: list[str],
    comments: list[dict[str, Any]],
    context_questions: list[str],
    alias: dict[str, Any],
    risk: dict[str, Any],
) -> str:
    for comment in comments:
        proposal = comment.get("file_fix_proposal")
        if proposal:
            return str(proposal)
    if "identity" in " ".join(questions).lower() or alias.get("status") == "no_alias_record":
        return "I think the fix is to refresh my alias record and verify imports against my current path."
    if "over_cap" in risk.get("items", []):
        return "I think the fix is to split me at stable function boundaries, then update lineage before tests run."
    if context_questions:
        return "I think the fix is to answer my pending context questions with docstrings or a focused test."
    return "I think the fix is to keep my current role, but record this interview as fresh operator-visible context."
