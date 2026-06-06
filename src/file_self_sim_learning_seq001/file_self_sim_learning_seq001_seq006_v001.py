"""file_self_sim_learning_seq001_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq040_v001 import _add
from pathlib import Path
from typing import Any
import re

def _seed_from_prompt_contract_fallback(root: Path, bucket: dict[str, dict[str, Any]]) -> None:
    for rel in [
        "codex_compat.py",
        "src/batch_rewrite_sim_seq001_v001.py",
        "src/file_self_sim_learning_seq001_v001.py",
        "src/file_email_plugin_seq001_v001.py",
        "src/intent_loop_closer_seq001_v001.py",
    ]:
        if (root / rel).exists():
            _add(bucket, rel, 2.0, "prompt contract fallback woke core self-fix file", "prompt_contract")


def _seed_from_proposals(bucket: dict[str, dict[str, Any]], sources: dict[str, Any]) -> None:
    for index, proposal in enumerate((sources.get("latest") or {}).get("proposals") or []):
        rel = _clean_rel(proposal.get("path"))
        if not rel:
            continue
        points = 9.0 - index * 0.35
        points += float(proposal.get("confidence") or 0) * 2.0
        points += float(proposal.get("interlink_score") or 0) * 2.0
        _add(bucket, rel, points, "batch proposal survived intent/history ranking", "proposal")
        bucket[rel]["proposal"] = proposal


def _seed_from_council(bucket: dict[str, dict[str, Any]], sources: dict[str, Any]) -> None:
    council = sources.get("council") or {}
    for job in council.get("jobs") or []:
        captain = _clean_rel(job.get("captain"))
        if captain:
            _add(bucket, captain, 3.5, "job captain should wake first", "council")
        for rel in (job.get("files") or [])[:12]:
            _add(bucket, rel, 2.4, "job member in same work cell", "council")
        for rel in (job.get("context_files") or [])[:12]:
            _add(bucket, rel, 1.1, "context vein from job council", "council")
    for pack in council.get("context_packs") or []:
        for rel in (pack.get("files") or [])[:16]:
            _add(bucket, rel, 0.9, f"context pack {pack.get('pack_id', 'unknown')}", "context_pack")


def _seed_from_memory(bucket: dict[str, dict[str, Any]], sources: dict[str, Any]) -> None:
    for item in (sources.get("memory_index") or {}).get("files") or []:
        rel = _clean_rel(item.get("file"))
        if rel:
            _add(bucket, rel, 2.0, "file has durable mail/thread memory", "memory")
