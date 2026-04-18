"""测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_score_composition_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 38 lines | ~370 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def score_rework_from_composition(composition: dict) -> dict:
    """Score rework from chat composition data (deleted words, rewrites).

    Composition data captures actual prompt-level deletions and rewrites —
    the high-fidelity path. When the operator deletes half their prompt and
    rewrites it, that's rework regardless of what the final text looks like.
    """
    del_ratio = composition.get('deletion_ratio', 0)
    rewrites = len(composition.get('rewrites', []))
    deleted_words = composition.get('deleted_words', [])
    duration_ms = max(composition.get('duration_ms', 1), 1)
    total_keys = max(composition.get('total_keystrokes', 1), 1)

    # Each rewrite adds 0.15 (capped at 0.45), deletion ratio adds up to 0.55
    rewrite_weight = min(rewrites * 0.15, 0.45)
    del_weight = del_ratio * 0.55
    rework_score = round(min(1.0, del_weight + rewrite_weight), 3)

    wpm = round((total_keys / 5) / max(duration_ms / 60_000, 0.001), 1)

    if rework_score > 0.45 or del_ratio > HEAVY_DEL_RATIO:
        verdict = 'miss'
    elif rework_score > 0.20 or rewrites >= 2:
        verdict = 'partial'
    else:
        verdict = 'ok'

    return {
        'rework_score': rework_score,
        'del_ratio': round(del_ratio, 3),
        'wpm': wpm,
        'verdict': verdict,
    }


HEAVY_DEL_RATIO  = 0.35     # deletion rate threshold for "rework"
