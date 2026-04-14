"""unsaid_accumulator_record_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 21 lines | ~222 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json

def record(fragment: str, completed_intent: str,
           deleted_words: list[str] | None = None,
           unsaid_threads: list[str] | None = None,
           context: str = 'code') -> dict:
    """Persist an unsaid thread entry. Returns the stored entry."""
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'fragment': fragment[:500],
        'completed_intent': completed_intent[:500],
        'deleted_words': (deleted_words or [])[:20],
        'unsaid_threads': (unsaid_threads or [])[:10],
        'context': context,
    }
    UNSAID_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(UNSAID_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry
