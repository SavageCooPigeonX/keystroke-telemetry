"""drift_seq003_compute_baseline_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v003 | 62 lines | ~557 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 2
# ──────────────────────────────────────────────
from collections import Counter
import time

def compute_baseline(operator_id: str) -> dict:
    """Compute operator typing baseline from history.

    Returns:
        {
            'avg_hesitation': float,
            'avg_wpm': float,
            'abandonment_rate': float,
            'dominant_state': str,
            'total_messages': int,
            'frustration_rate': float,
            'flow_rate': float,
        }
    """
    cached = _baseline_cache.get(operator_id)
    if cached and time.time() - cached['ts'] < BASELINE_CACHE_TTL:
        return cached['baseline']

    baseline = {
        'avg_hesitation': 0.0, 'avg_wpm': 0.0, 'abandonment_rate': 0.0,
        'dominant_state': 'neutral', 'total_messages': 0,
        'frustration_rate': 0.0, 'flow_rate': 0.0,
    }

    rows = _store.fetch_history(operator_id)
    if not rows:
        _baseline_cache[operator_id] = {'baseline': baseline, 'ts': time.time()}
        return baseline

    n = len(rows)
    baseline['total_messages'] = n
    baseline['avg_hesitation'] = round(sum(r.get('hesitation_score', 0) for r in rows) / n, 3)

    wpm_vals = [r.get('wpm', 0) for r in rows if r.get('wpm', 0) > 0]
    baseline['avg_wpm'] = round(sum(wpm_vals) / max(len(wpm_vals), 1), 1)

    states = [r.get('cognitive_state', 'neutral') for r in rows]
    submitted_count = sum(1 for r in rows if r.get('submitted'))
    baseline['abandonment_rate'] = round(1 - (submitted_count / n), 3) if n else 0

    state_counts = Counter(states)
    baseline['dominant_state'] = state_counts.most_common(1)[0][0] if state_counts else 'neutral'
    baseline['frustration_rate'] = round(state_counts.get('frustrated', 0) / n, 3)
    baseline['flow_rate'] = round(state_counts.get('flow', 0) / n, 3)

    _baseline_cache[operator_id] = {'baseline': baseline, 'ts': time.time()}
    return baseline


BASELINE_CACHE_TTL = 300
