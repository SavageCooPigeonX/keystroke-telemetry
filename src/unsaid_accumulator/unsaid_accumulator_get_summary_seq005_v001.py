"""unsaid_accumulator_get_summary_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 16 lines | ~168 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def get_summary(max_threads: int = 10) -> str:
    """Compressed summary of recent unsaid threads for LLM context."""
    recent = get_recent(max_threads)
    if not recent:
        return ''
    parts = [f'Unsaid thread history ({len(recent)} recent):']
    for entry in recent:
        intent = entry.get('completed_intent', '')[:80]
        ctx = entry.get('context', 'code')
        parts.append(f'- [{ctx}] {intent}')
        deleted = entry.get('deleted_words', [])
        if deleted:
            parts.append(f'  deleted: {", ".join(deleted[:5])}')
    return '\n'.join(parts)
