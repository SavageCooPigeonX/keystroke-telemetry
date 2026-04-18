"""路f_cxr_s027_v002_d0330_缩分话_λF_route_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 30 lines | ~244 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from src.片w_sm_s026_v002_d0330_缩分话_λF import (
    SHARD_SCHEMA, read_shard_entries, get_shard_summary, list_shards,
    get_unresolved_contradictions,
)
from .p_路csvd缩λs_s004_v001 import MIN_RELEVANCE, TOP_N_DEFAULT, score_shard
import re

def route_context(root: Path, query: str, top_n: int = TOP_N_DEFAULT) -> list[dict]:
    """Score all shards, return top-N with summaries.

    Returns list of {name, relevance, summary} dicts, sorted by relevance desc.
    """
    root = Path(root)
    existing = list_shards(root)
    if not existing:
        return []

    scored = []
    for name in existing:
        rel = score_shard(query, name, root)
        if rel >= MIN_RELEVANCE:
            scored.append({
                'name': name,
                'relevance': round(rel, 3),
                'summary': get_shard_summary(root, name),
            })

    scored.sort(key=lambda x: -x['relevance'])
    return scored[:top_n]
