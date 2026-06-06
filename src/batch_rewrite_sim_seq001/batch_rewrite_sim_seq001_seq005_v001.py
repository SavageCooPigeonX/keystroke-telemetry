"""batch_rewrite_sim_seq001_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq006_v001 import _job_council_member
from .batch_rewrite_sim_seq001_seq008_v001 import _dedupe_strings
from .batch_rewrite_sim_seq001_seq009_v001 import _context_packs
from .batch_rewrite_sim_seq001_seq010_v001 import _job_why
from .batch_rewrite_sim_seq001_seq011_v001 import _job_council_summary
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import hashlib
import os
import re

def _file_job_council(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    proposals = [item for item in (result.get("proposals") or []) if isinstance(item, dict)]
    intent = result.get("intent") or {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    roster = []
    relationships = []
    for index, proposal in enumerate(proposals):
        member = _job_council_member(root, proposal, index)
        roster.append(member)
        grouped[member["scope"]].append(member)
        for friend in member.get("friendships", []):
            relationships.append({
                "from": member["file"],
                "to": friend,
                "type": "friendship",
                "reason": "shared context pack wants both files loaded",
            })
        for target in member.get("beefs", []):
            relationships.append({
                "from": member["file"],
                "to": target,
                "type": "beef",
                "reason": "compatibility report says rewrite order matters",
            })

    jobs = []
    for scope, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        captain = max(members, key=lambda item: (item.get("interlink_score", 0), item.get("confidence", 0)))
        failed = sum(int(item.get("failed_checks", 0)) for item in members)
        passed = sum(int(item.get("passed_checks", 0)) for item in members)
        files = _dedupe_strings([member["file"] for member in members])
        context_files = _dedupe_strings(
            [file_name for member in members for file_name in member.get("context_files", [])]
        )
        total_tokens = sum(int(member.get("approx_tokens") or 0) for member in members)
        job_id = "job-" + hashlib.sha256(
            f"{intent.get('intent_key', '')}|{scope}|{','.join(files)}".encode("utf-8")
        ).hexdigest()[:10]
        jobs.append({
            "job_id": job_id,
            "scope": scope,
            "goal": f"{intent.get('verb', 'route')} `{scope}` toward `{result.get('target_state', 'interlinked_source_state')}`",
            "captain": captain["file"],
            "files": files,
            "context_files": context_files,
            "total_estimated_tokens": total_tokens,
            "passed_checks": passed,
            "failed_checks": failed,
            "status": "ready_for_operator_approval" if failed == 0 else "needs_context_or_repair",
            "why": _job_why(scope, members, failed),
        })

    context_packs = _context_packs(root, proposals, roster, jobs)
    total_tokens = sum(int(member.get("approx_tokens") or 0) for member in roster)
    return {
        "schema": "file_job_council/v1",
        "ts": result.get("ts"),
        "intent_key": intent.get("intent_key", ""),
        "target_state": result.get("target_state", "interlinked_source_state"),
        "total_proposals": len(proposals),
        "total_estimated_tokens": total_tokens,
        "jobs": jobs,
        "context_packs": context_packs,
        "relationships": relationships[:80],
        "roster": roster[:40],
        "comedy_summary": _job_council_summary(jobs, relationships, roster),
    }
