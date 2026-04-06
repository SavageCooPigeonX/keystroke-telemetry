"""drift_seq003_build_cognitive_context_seq004_v001.py — Auto-extracted by Pigeon Compiler."""


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
