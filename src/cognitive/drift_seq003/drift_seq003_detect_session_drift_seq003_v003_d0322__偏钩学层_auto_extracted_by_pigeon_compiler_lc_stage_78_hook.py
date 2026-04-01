"""drift_seq003_detect_session_drift_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v003 | 69 lines | ~677 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 2
# ──────────────────────────────────────────────

def detect_session_drift(session_summaries: list, baseline: dict) -> dict:
    """Compare this session's patterns against operator baseline.

    Args:
        session_summaries: List of message summary dicts (most recent first)
        baseline: From compute_baseline()

    Returns:
        {
            'hesitation_drift': float,       # -1 to +1
            'wpm_drift': float,              # -1 to +1
            'frustration_escalating': bool,
            'flow_streak': int,
            'engagement_trend': str,         # improving, declining, stable
        }
    """
    drift = {
        'hesitation_drift': 0.0,
        'wpm_drift': 0.0,
        'frustration_escalating': False,
        'flow_streak': 0,
        'engagement_trend': 'stable',
    }

    if not session_summaries:
        return drift

    session_hes = sum(r.get('hesitation_score', 0) for r in session_summaries) / len(session_summaries)
    session_wpm_vals = [r.get('wpm', 0) for r in session_summaries if r.get('wpm', 0) > 0]
    session_wpm = sum(session_wpm_vals) / max(len(session_wpm_vals), 1)

    base_hes = baseline.get('avg_hesitation', 0) or 0.001
    base_wpm = baseline.get('avg_wpm', 0) or 0.001

    drift['hesitation_drift'] = round(min(max((session_hes - base_hes) / max(base_hes, 0.01), -1), 1), 3)
    drift['wpm_drift'] = round(min(max((session_wpm - base_wpm) / max(base_wpm, 0.1), -1), 1), 3)

    # Frustration escalation — last 5 messages
    recent_states = [r.get('cognitive_state', 'neutral') for r in session_summaries[:5]]
    drift['frustration_escalating'] = sum(1 for s in recent_states if s in ('frustrated', 'abandoned')) >= 3

    # Flow streak
    for r in session_summaries:
        if r.get('cognitive_state') in ('flow', 'focused'):
            drift['flow_streak'] += 1
        else:
            break

    # Engagement trend
    if len(session_summaries) >= 4:
        mid = len(session_summaries) // 2
        recent_hes = sum(r.get('hesitation_score', 0) for r in session_summaries[:mid]) / mid
        earlier_hes = sum(r.get('hesitation_score', 0) for r in session_summaries[mid:]) / (len(session_summaries) - mid)
        if recent_hes < earlier_hes - 0.1:
            drift['engagement_trend'] = 'improving'
        elif recent_hes > earlier_hes + 0.1:
            drift['engagement_trend'] = 'declining'

    return drift
