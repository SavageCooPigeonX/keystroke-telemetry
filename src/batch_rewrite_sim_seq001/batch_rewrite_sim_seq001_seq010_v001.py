"""batch_rewrite_sim_seq001_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq008_v001 import _dedupe_strings
from .batch_rewrite_sim_seq001_seq008_v001 import _estimate_file_tokens
from pathlib import Path
from typing import Any
import os
import re

def _context_pack(root: Path, pack_id: str, purpose: str, files: list[str], token_budget: int) -> dict[str, Any]:
    selected = []
    skipped = []
    total = 0
    for file_name in _dedupe_strings(files):
        tokens = _estimate_file_tokens(root, file_name)
        if selected and total + tokens > token_budget:
            skipped.append({"file": file_name, "estimated_tokens": tokens, "reason": "context pack token budget"})
            continue
        selected.append(file_name)
        total += tokens
    return {
        "pack_id": pack_id,
        "purpose": purpose,
        "token_budget": token_budget,
        "files": selected,
        "total_estimated_tokens": total,
        "skipped_files": skipped[:20],
    }


def _job_why(scope: str, members: list[dict[str, Any]], failed: int) -> str:
    if failed:
        loud = max(members, key=lambda item: int(item.get("failed_checks") or 0))
        return f"`{scope}` needs repair/context because `{loud.get('file')}` failed {loud.get('failed_checks')} checks"
    captain = max(members, key=lambda item: (item.get("interlink_score", 0), item.get("confidence", 0)))
    return f"`{scope}` is coherent enough for approval; `{captain.get('file')}` is carrying the intent"
