"""query_memory_seq010_clustering_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v002 | 27 lines | ~258 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def cluster_unsaid_threads(texts: list[str], threshold: float = 0.25) -> list[dict]:
    """Group unsaid fragment texts by trigram similarity.

    Returns list of clusters: [{label: str, members: [str], size: int}]
    Label is the longest/most informative text in each cluster.
    Greedy single-pass — O(n^2) but n is always small (≤50 abandons).
    """
    if not texts:
        return []
    clusters: list[list[str]] = []
    for text in texts:
        placed = False
        for cluster in clusters:
            # Compare against cluster representative (first member)
            if _trigram_similarity(text, cluster[0]) >= threshold:
                cluster.append(text)
                placed = True
                break
        if not placed:
            clusters.append([text])
    return [
        {'label': max(c, key=len), 'members': c, 'size': len(c)}
        for c in sorted(clusters, key=len, reverse=True)
    ]
