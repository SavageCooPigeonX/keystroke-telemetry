"""隐p_un_s002_v002_d0315_缩分话_λν_topic_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 9 lines | ~128 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _extract_topic(text: str) -> str:
    """Extract a rough topic label from text (first few meaningful words)."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'you', 'can', 'how'}
    meaningful = [w for w in words if w not in stopwords][:4]
    return ' '.join(meaningful) if meaningful else text[:30].strip()
