"""batch_rewrite_sim_seq001_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq008_v001 import _dedupe_strings
from .batch_rewrite_sim_seq001_seq010_v001 import _context_pack
from pathlib import Path
from typing import Any
import json
import os
import re

def _context_packs(
    root: Path,
    proposals: list[dict[str, Any]],
    roster: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    primary = _dedupe_strings(
        [str(prop.get("path") or "") for prop in proposals[:4]]
        + [item for prop in proposals[:4] for item in (prop.get("context_injection") or [])]
    )
    validation = _dedupe_strings(
        item
        for prop in proposals
        for item in _validation_context_files(prop)
    )
    relationship = _dedupe_strings(
        item
        for member in roster
        for item in [*member.get("friendships", []), *member.get("beefs", [])]
    )
    job_files = _dedupe_strings(
        item
        for job in jobs
        for item in [*job.get("files", []), *job.get("context_files", [])]
    )
    packs = [
        _context_pack(root, "pack-primary", "load first for the code completion pass", primary[:12], 24000),
        _context_pack(root, "pack-validation", "load when compile/test gates are being judged", validation[:12], 16000),
        _context_pack(root, "pack-relationships", "load to explain friendships, conflicts, and import edges", relationship[:16], 24000),
        _context_pack(root, "pack-job-all", "bounded full job context for the current sim", job_files[:24], 48000),
    ]
    return [pack for pack in packs if pack.get("files")]


def _validation_context_files(proposal: dict[str, Any]) -> list[str]:
    out = []
    for step in proposal.get("validation_plan") or []:
        for match in re.findall(r"[A-Za-z0-9_./\\-]+\.(?:py|json|md|ts|tsx|js)", str(step)):
            out.append(match.replace("\\", "/"))
    return out
