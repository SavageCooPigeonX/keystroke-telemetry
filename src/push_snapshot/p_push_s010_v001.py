"""push_snapshot_seq001_v001_coupling_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 21 lines | ~196 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _compute_coupling(registry: dict) -> dict:
    """Extract coupling stats from registry bug_keys."""
    high_pairs = 0
    coupling_scores = []
    for m in registry.values():
        if not isinstance(m, dict):
            continue
        bugs = m.get('bug_keys', [])
        if 'high_coupling' in bugs:
            high_pairs += 1
        bc = m.get('bug_counts', {})
        if bc.get('high_coupling', 0) > 0:
            coupling_scores.append(bc['high_coupling'])
    avg = sum(coupling_scores) / len(coupling_scores) if coupling_scores else 0
    return {
        'high_pairs': high_pairs,
        'avg_coupling': round(avg, 3),
        'max_coupling': max(coupling_scores, default=0),
    }
