"""unsaid_accumulator_seq001_v001_get_recent_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 12 lines | ~105 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json

def get_recent(n: int = 10) -> list[dict]:
    """Last N unsaid entries."""
    if not UNSAID_LOG.exists():
        return []
    try:
        lines = UNSAID_LOG.read_text('utf-8', errors='ignore').strip().split('\n')
        return [json.loads(l) for l in lines[-n:] if l.strip()]
    except Exception:
        return []
