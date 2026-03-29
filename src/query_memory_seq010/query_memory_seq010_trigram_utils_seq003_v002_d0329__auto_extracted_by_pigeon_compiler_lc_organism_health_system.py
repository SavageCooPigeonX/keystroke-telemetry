"""query_memory_seq010_trigram_utils_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 15 lines | ~138 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _trigrams(text: str) -> set[str]:
    """Character trigrams for similarity computation."""
    t = re.sub(r'\s+', ' ', text.lower().strip())
    return {t[i:i+3] for i in range(len(t) - 2)} if len(t) >= 3 else set()


def _trigram_similarity(a: str, b: str) -> float:
    """Jaccard similarity over character trigrams."""
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)
