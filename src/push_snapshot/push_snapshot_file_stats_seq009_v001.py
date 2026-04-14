"""push_snapshot_file_stats_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 27 lines | ~310 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _compute_file_stats(root: Path, registry: dict) -> dict:
    # Registry stores token counts (~10 tokens/line for Python).
    # Pigeon standard: 50-line target, 200-line hard cap.
    # Token equivalents: 500 tokens ≈ 50 lines, 2000 tokens ≈ 200 lines.
    TOKEN_TARGET = 500   # ≈ 50 lines
    TOKEN_CAP = 2000     # ≈ 200 lines

    tokens = [m.get('tokens', 0) for m in registry.values() if isinstance(m, dict)]
    if not tokens:
        return {'avg_tokens': 0, 'median_tokens': 0, 'max_tokens': 0,
                'total_tokens': 0, 'under_50': 0, 'range_50_200': 0,
                'over_200': 0, 'compliant': 0}
    tokens.sort()
    median = tokens[len(tokens) // 2]
    return {
        'avg_tokens': round(sum(tokens) / len(tokens), 1),
        'median_tokens': median,
        'max_tokens': max(tokens),
        'total_tokens': sum(tokens),
        'under_50': sum(1 for t in tokens if t <= TOKEN_TARGET),
        'range_50_200': sum(1 for t in tokens if TOKEN_TARGET < t <= TOKEN_CAP),
        'over_200': sum(1 for t in tokens if t > TOKEN_CAP),
        'compliant': sum(1 for t in tokens if t <= TOKEN_CAP),
    }
