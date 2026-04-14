"""u_pd_s024_v001_section_text_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 17 lines | ~228 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _section_text(snap: dict, block: str) -> str:
    """Extract text representing `block` from a snapshot.
    block='features' → JSON dump of features dict.
    Otherwise → 'present' / 'absent' + snapshot metadata.
    """
    if block.lower() == 'features':
        feats = snap.get('features', {})
        return '\n'.join(f'  {k}: {v}' for k, v in sorted(feats.items()))
    sections = snap.get('sections', [])
    matched = [s for s in sections if block.lower() in s.lower()]
    if not matched:
        return f'(section not present in commit {snap.get("commit","?")})'
    # Represent as "section header + lines count" — we don't store per-section text
    meta = snap.get('commit', '?')[:7]
    return '\n'.join(f'  [{meta}] {s}  ({snap.get("lines","?")} total lines, {snap.get("bytes","?")} bytes)' for s in matched)
