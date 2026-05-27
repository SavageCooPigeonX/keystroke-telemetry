"""Cognitive Drift Detector — tracks operator typing patterns across sessions.

Compares current session typing against historic baselines to detect:
  - Hesitation drift (more/less hesitant than usual)
  - WPM drift (faster/slower than normal)
  - Frustration escalation (3+ frustrated states in last 5 messages)
  - Flow streaks (consecutive flow/focused states)
  - Engagement trends (improving, declining, stable)

Standalone version — uses in-memory baseline storage.
For production with persistence, swap _store with your database adapter.
"""

import time
import logging
from collections import Counter

logger = logging.getLogger('keystroke_telemetry.cognitive')

# ── In-memory baseline store (swap for DB in production) ──
_baseline_cache: dict = {}
BASELINE_CACHE_TTL = 300


class BaselineStore:
    """In-memory operator baseline storage.

    Override fetch_history() to pull from your database instead.
    """

    def __init__(self):
        self._sessions: dict = {}  # operator_id -> [summary_dicts]

    def record(self, operator_id: str, summary: dict):
        """Record a message summary for baseline computation."""
        if operator_id not in self._sessions:
            self._sessions[operator_id] = []
        self._sessions[operator_id].append(summary)
        # Keep last 200
        if len(self._sessions[operator_id]) > 200:
            self._sessions[operator_id] = self._sessions[operator_id][-200:]

    def fetch_history(self, operator_id: str, limit: int = 200) -> list:
        """Fetch historic summaries for an operator."""
        return (self._sessions.get(operator_id) or [])[-limit:]


# Default store instance
_store = BaselineStore()


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


def build_cognitive_context(session_summaries: list, operator_id: str,
                            current_state: str = 'neutral') -> dict:
    """Build full cognitive context block for prompt injection.

    Args:
        session_summaries: This session's message summaries (most recent first)
        operator_id: Unique operator identifier
        current_state: Current cognitive state label

    Returns:
        {
            'cognitive_block': str,       # Formatted text for prompt injection
            'drift': dict,
            'baseline': dict,
            'adaptation_flags': list[str],
        }
    """
    baseline = compute_baseline(operator_id)
    drift = detect_session_drift(session_summaries, baseline)

    flags = []
    if drift.get('frustration_escalating'):
        flags.append('FRUSTRATION_ESCALATING')
    if drift.get('flow_streak', 0) >= 3:
        flags.append('DEEP_FLOW')
    if drift.get('engagement_trend') == 'declining':
        flags.append('ENGAGEMENT_DECLINING')
    if drift.get('engagement_trend') == 'improving':
        flags.append('ENGAGEMENT_IMPROVING')
    if baseline.get('abandonment_rate', 0) > 0.3:
        flags.append('HIGH_ABANDONMENT_HISTORY')
    if current_state in ('frustrated', 'abandoned'):
        flags.append('ACUTE_FRUSTRATION')
    if current_state == 'hesitant' and drift.get('hesitation_drift', 0) > 0.3:
        flags.append('HESITATION_ABOVE_BASELINE')

    # Build prompt block
    lines = ['--- COGNITIVE TELEMETRY ---']
    if current_state != 'neutral':
        lines.append(f'Current typing state: {current_state}')
    if session_summaries:
        lines.append(f'Session messages tracked: {len(session_summaries)}')
        if drift.get('engagement_trend') != 'stable':
            lines.append(f'Engagement trend: {drift["engagement_trend"]}')
    if baseline.get('total_messages', 0) > 5:
        lines.append(f'Operator baseline: avg hesitation={baseline["avg_hesitation"]}, '
                      f'avg wpm={baseline["avg_wpm"]}, '
                      f'abandonment rate={baseline["abandonment_rate"]}')
        if drift.get('hesitation_drift', 0) > 0.2:
            lines.append(f'Warning: Hesitation {drift["hesitation_drift"]:+.2f} above baseline')
        elif drift.get('hesitation_drift', 0) < -0.2:
            lines.append(f'OK: Hesitation {drift["hesitation_drift"]:+.2f} below baseline (more confident)')
    if flags:
        lines.append(f'Adaptation flags: {", ".join(flags)}')
    if drift.get('frustration_escalating'):
        lines.append('WARNING: OPERATOR FRUSTRATION ESCALATING — prioritize clarity, be direct')
    if drift.get('flow_streak', 0) >= 3:
        lines.append('OK: Operator in sustained flow — match depth, go substantive')
    lines.append('--- END COGNITIVE TELEMETRY ---')

    return {
        'cognitive_block': '\n'.join(lines),
        'drift': drift,
        'baseline': baseline,
        'adaptation_flags': flags,
    }
