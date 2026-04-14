"""unsaid_accumulator_query_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 23 lines | ~226 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json

def query(topic: str = '', limit: int = 20) -> list[dict]:
    """Search unsaid history by topic keyword."""
    if not UNSAID_LOG.exists():
        return []
    results = []
    topic_lower = topic.lower()
    try:
        for line in UNSAID_LOG.read_text('utf-8', errors='ignore').strip().split('\n'):
            if not line.strip():
                continue
            entry = json.loads(line)
            if not topic or topic_lower in entry.get('completed_intent', '').lower() \
                    or topic_lower in entry.get('fragment', '').lower() \
                    or any(topic_lower in t.lower() for t in entry.get('unsaid_threads', [])):
                results.append(entry)
            if len(results) >= limit:
                break
    except Exception:
        pass
    return results
