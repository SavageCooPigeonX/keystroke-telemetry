"""push_snapshot_self_fix_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 33 lines | ~280 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _load_self_fix_counts(root: Path) -> dict:
    """Parse latest self-fix report for bug category counts."""
    sf_dir = root / 'docs' / 'self_fix'
    if not sf_dir.exists():
        return {'total': 0}
    files = sorted(sf_dir.glob('*.md'))
    if not files:
        return {'total': 0}
    latest = files[-1]
    text = latest.read_text('utf-8', errors='ignore')

    counts: dict[str, int] = {'total': 0, 'other': 0}
    categories = ['hardcoded_import', 'over_hard_cap', 'dead_export',
                   'high_coupling', 'duplicate_docstring', 'query_noise']
    for cat in categories:
        counts[cat] = 0

    import re
    # Count by scanning for category markers
    for cat in categories:
        matches = re.findall(rf'\b{cat}\b', text)
        counts[cat] = len(matches)
        counts['total'] += len(matches)

    # Try to extract total from "Problems Found: N" line
    m = re.search(r'Problems Found:\s*(\d+)', text)
    if m:
        counts['total'] = int(m.group(1))

    return counts
