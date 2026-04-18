"""push_snapshot_seq001_v001_compute_drift_decomposed_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 104 lines | ~1,019 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path

def compute_drift(root: Path, current: dict, previous: dict | None = None) -> dict:
    """Compute drift between two snapshots.

    If no previous snapshot given, loads the most recent one.
    Returns deltas for every metric — positive = grew, negative = shrank.
    """
    if previous is None:
        previous = _load_previous_snapshot(root, current.get('commit', ''))

    if not previous:
        return {'status': 'first_snapshot', 'drift': {}}

    drift = {}

    # Module drift
    drift['modules_delta'] = current['modules']['total'] - previous['modules']['total']
    drift['compliance_delta'] = round(
        current['modules']['compliance_pct'] - previous['modules']['compliance_pct'], 1)
    drift['over_cap_delta'] = current['modules']['over_cap'] - previous['modules']['over_cap']

    # Bug drift
    drift['bugs_delta'] = current['bugs']['total'] - previous['bugs']['total']
    drift['bugs_new'] = max(0, drift['bugs_delta'])
    drift['bugs_fixed'] = max(0, -drift['bugs_delta'])
    drift['hardcoded_import_delta'] = (
        current['bugs']['hardcoded_import'] - previous['bugs']['hardcoded_import'])

    # File size drift
    drift['avg_tokens_delta'] = round(
        current['file_stats']['avg_tokens'] - previous['file_stats']['avg_tokens'], 1)
    drift['total_tokens_delta'] = (
        current['file_stats']['total_tokens'] - previous['file_stats']['total_tokens'])
    drift['bloat_direction'] = (
        'bloating' if drift['avg_tokens_delta'] > 10
        else 'compressing' if drift['avg_tokens_delta'] < -10
        else 'stable')

    # Coupling drift
    drift['coupling_delta'] = round(
        current['coupling']['avg_coupling'] - previous['coupling']['avg_coupling'], 3)
    drift['high_coupling_delta'] = (
        current['coupling']['high_coupling_pairs'] - previous['coupling']['high_coupling_pairs'])

    # Death drift
    drift['deaths_delta'] = current['deaths']['total'] - previous['deaths']['total']

    # Heat drift
    drift['avg_hes_delta'] = round(
        current['heat']['avg_hesitation'] - previous['heat']['avg_hesitation'], 3)

    # Operator drift
    drift['wpm_delta'] = round(
        current['operator']['avg_wpm'] - previous['operator']['avg_wpm'], 1)
    drift['deletion_delta'] = round(
        current['operator']['avg_deletion'] - previous['operator']['avg_deletion'], 3)

    # Sync drift
    drift['sync_delta'] = round(
        current['cycle']['sync_score'] - previous['cycle']['sync_score'], 3)

    # Probe drift
    drift['probes_delta'] = (
        current['probes']['total_conversations'] - previous['probes']['total_conversations'])
    drift['intents_delta'] = (
        current['probes']['total_intents_extracted'] - previous['probes']['total_intents_extracted'])

    # Overall health score (0-100)
    drift['health_score'] = _compute_health_score(current)
    drift['prev_health_score'] = _compute_health_score(previous)
    drift['health_delta'] = round(drift['health_score'] - drift['prev_health_score'], 1)

    # Health direction
    if drift['health_delta'] > 2:
        drift['health_direction'] = 'improving'
    elif drift['health_delta'] < -2:
        drift['health_direction'] = 'degrading'
    else:
        drift['health_direction'] = 'stable'

    # Time between pushes
    try:
        t_cur = datetime.fromisoformat(current['ts'])
        t_prev = datetime.fromisoformat(previous['ts'])
        drift['hours_since_last_push'] = round((t_cur - t_prev).total_seconds() / 3600, 1)
    except Exception:
        drift['hours_since_last_push'] = None

    # Mutation summary (what changed most)
    drift['biggest_moves'] = _biggest_moves(drift)

    result = {
        'status': 'computed',
        'current_commit': current.get('commit', ''),
        'previous_commit': previous.get('commit', ''),
        'drift': drift,
    }

    # Persist to drift log
    _append_drift_log(root, result)
    return result
