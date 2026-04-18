"""路f_cxr_s027_v002_d0330_缩分话_λF_score_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 45 lines | ~414 tokens
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
from .路f_cxr_s027_v002_d0330_缩分话_λF_tokenize_seq002_v001 import _tokenize
import re

def score_shard(query: str, shard_name: str, root: Path) -> float:
    """Score relevance of a shard to the current query. Returns 0-1."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    # 1. Schema description match (does the shard topic relate to the query?)
    desc = SHARD_SCHEMA.get(shard_name, '')
    desc_tokens = _tokenize(desc)
    desc_overlap = len(query_tokens & desc_tokens) / max(len(query_tokens), 1)

    # 2. Entry content match (do stored patterns match query words?)
    entries = read_shard_entries(root, shard_name)
    if not entries:
        return desc_overlap * 0.3  # empty shard — only schema match counts

    content_score = 0.0
    recent_entries = entries[-20:]  # only check recent entries
    for e in recent_entries:
        # strip timestamp prefix
        text = re.sub(r'^`[^`]*`\s*', '', e)
        entry_tokens = _tokenize(text)
        overlap = len(query_tokens & entry_tokens)
        if overlap:
            content_score += overlap / max(len(query_tokens), 1)
    content_score = min(content_score / max(len(recent_entries), 1), 1.0)

    # 3. Entry count signal — shards with more data are more likely useful
    density = min(len(entries) / 50, 0.15)

    score = (desc_overlap * 0.35) + (content_score * 0.45) + density
    return min(score, 1.0)


TOP_N_DEFAULT = 5

MIN_RELEVANCE = 0.05
