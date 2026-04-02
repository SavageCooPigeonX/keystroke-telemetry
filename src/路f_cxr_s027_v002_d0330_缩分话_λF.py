"""context_router_seq027_v001.py — Shard relevance scorer + context injector.

Scores which memory shards are relevant to the current prompt, pulls top-N,
and formats them for injection into the enricher's DeepSeek context window.

Zero LLM calls — pure keyword/trigram scoring with recency boost.
Reads markdown shards from logs/shards/*.md.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 027 | VER: v002 | 137 lines | ~1,216 tokens
# DESC:   shard_relevance_scorer_context_injector
# INTENT: gemini_flash_enricher
# LAST:   2026-03-30 @ 5018891
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-30T07:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  update for markdown shards + contradiction awareness
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations
import re
from pathlib import Path

from src.片w_sm_s026_v002_d0330_缩分话_λF import (
    SHARD_SCHEMA, read_shard_entries, get_shard_summary, list_shards,
    get_unresolved_contradictions,
)

TOP_N_DEFAULT = 5
MIN_RELEVANCE = 0.05


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'\b\w{3,}\b', text.lower()))


def _trigrams(text: str) -> set[str]:
    words = re.findall(r'\b\w{3,}\b', text.lower())
    return set(f'{words[i]} {words[i+1]} {words[i+2]}' for i in range(len(words) - 2))


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


def format_shard_context(routed: list[dict], root: Path | None = None) -> str:
    """Format routed shards into a text block for the enricher prompt.

    If root is provided, also appends unresolved contradictions as warnings.
    """
    if not routed:
        return ''
    lines = ['MEMORY SHARDS (learned patterns from operator history):']
    for r in routed:
        if r['summary']:
            lines.append(f"  [{r['name']}] (relevance={r['relevance']})")
            for sline in r['summary'].splitlines()[1:]:  # skip header
                lines.append(f'  {sline}')

    # append contradiction warnings if any
    if root:
        contras = get_unresolved_contradictions(root)
        if contras:
            lines.append('')
            lines.append(f'⚠ CONTRADICTIONS ({len(contras)} unresolved):')
            for c in contras[:3]:  # top 3 only to save tokens
                lines.append(f"  [{c['shard']}] NEW: {c['new'][:60]} vs OLD: {c['old'][:60]}")

    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'fix import breaking after rename'
    print(f'Query: "{query}"\n')
    results = route_context(root, query)
    if results:
        print(format_shard_context(results))
    else:
        print('No shards found — run: py -m src.shard_manager_seq026_v001')
