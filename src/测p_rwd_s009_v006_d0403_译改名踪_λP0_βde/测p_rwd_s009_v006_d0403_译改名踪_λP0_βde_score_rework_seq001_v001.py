"""测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_score_rework_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 38 lines | ~410 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def score_rework(post_events: list) -> dict:
    """Score keystroke events from the post-response window.

    Returns:
        {rework_score: 0–1, del_ratio, wpm, verdict: 'miss'|'partial'|'ok'}
    """
    if not post_events:
        return {'rework_score': 0.0, 'del_ratio': 0.0, 'wpm': 0.0, 'verdict': 'ok'}

    inserts  = [e for e in post_events if e.get('type') == 'insert']
    deletes  = [e for e in post_events if e.get('type') == 'backspace']
    # del_ratio = deletes / (inserts + deletes) only — exclude pauses from denominator
    # so that a pause-heavy but delete-heavy window still scores as rework
    keystroke_total = max(len(inserts) + len(deletes), 1)
    del_ratio = len(deletes) / keystroke_total

    ts_vals  = [e['ts'] for e in post_events if 'ts' in e]
    dur_ms   = max((max(ts_vals) - min(ts_vals)) if len(ts_vals) > 1 else 1.0, 1.0)
    wpm      = round((len(inserts) / 5) / max(dur_ms / 60_000, 0.001), 1)

    # Rework score: high deletions early + slow typing = confused, rewriting
    speed_penalty = 0.15 * max(0, 1 - wpm / 40)  # 0.15 at 0 wpm, 0 at 40+ wpm
    rework_score = round(min(1.0, del_ratio * 0.7 + speed_penalty), 3)

    if rework_score > 0.55 or del_ratio > HEAVY_DEL_RATIO:
        verdict = 'miss'
    elif rework_score > 0.25:
        verdict = 'partial'
    else:
        verdict = 'ok'

    return {'rework_score': rework_score, 'del_ratio': round(del_ratio, 3),
            'wpm': wpm, 'verdict': verdict}


HEAVY_DEL_RATIO  = 0.35     # deletion rate threshold for "rework"
