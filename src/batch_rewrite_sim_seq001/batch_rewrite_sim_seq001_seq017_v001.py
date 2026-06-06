"""batch_rewrite_sim_seq001_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq020_v001 import _context_edges
from .batch_rewrite_sim_seq001_seq020_v001 import _dedupe_incompatibilities
from pathlib import Path
from typing import Any
import os
import re

def _reasoning_budget(decision: str) -> dict[str, str]:
    if decision == "blocked":
        return {"proposal": "quick", "grader": "quick", "deep_rewrite": "none"}
    return {"proposal": "quick", "grader": "focused", "deep_rewrite": "full_after_approval"}


def _attach_incompatibility_reports(proposals: list[dict[str, Any]]) -> None:
    for proposal in proposals:
        reports = []
        path = str(proposal.get("path") or "")
        edges = _context_edges(proposal)
        for other in proposals:
            other_path = str(other.get("path") or "")
            if not other_path or other_path == path:
                continue
            other_edges = _context_edges(other)
            shared = sorted((edges & other_edges) - {path, other_path})
            if shared:
                reports.append({
                    "with": other_path,
                    "severity": "medium",
                    "reason": f"shared context edge {shared[0]} means rewrite order or merged context is required",
                })
            if Path(path).name == "__init__.py" and str(other_path).startswith(str(Path(path).parent).replace("\\", "/")):
                reports.append({
                    "with": other_path,
                    "severity": "high",
                    "reason": "__init__ export layout can invalidate sibling rewrite assumptions",
                })
            if (proposal.get("cross_file_validation") or {}).get("dirty") and other_path in edges:
                reports.append({
                    "with": other_path,
                    "severity": "high",
                    "reason": "dirty working tree state must settle before peer rewrite is trusted",
                })
            if len(reports) >= 4:
                break
        proposal["incompatibilities"] = _dedupe_incompatibilities(reports)
