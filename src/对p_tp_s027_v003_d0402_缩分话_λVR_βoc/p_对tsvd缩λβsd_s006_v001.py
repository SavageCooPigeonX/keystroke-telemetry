"""对p_tp_s027_v003_d0402_缩分话_λVR_βoc_summary_decomposed_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def generate_cycle_summary(root: Path, cycle: dict | None = None) -> dict:
    """
    Generate a training summary for the push cycle.

    Reads all training_pairs since last push, scores intent alignment,
    and writes a summary to logs/training_cycle_summaries.jsonl.

    If `cycle` is provided (from run_push_cycle), it's merged into the summary.
    """
    root = Path(root)
    logs = root / 'logs'

    # Load all training pairs
    all_pairs = _load_jsonl_tail(logs / 'training_pairs.jsonl', max_lines=200)

    # Load push state to find cycle boundary
    state_path = logs / 'push_cycle_state.json'
    last_push_ts = ''
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding='utf-8'))
            last_push_ts = state.get('last_push_ts', '')
        except (json.JSONDecodeError, OSError):
            pass

    # Filter pairs from this cycle
    cycle_pairs = all_pairs  # default: all
    if last_push_ts:
        cycle_pairs = [p for p in all_pairs if p.get('ts', '') > last_push_ts]

    if not cycle_pairs:
        return {'status': 'no_pairs', 'count': 0}

    # Compute alignment metrics
    rework_scores = [
        p['alignment']['rework_score']
        for p in cycle_pairs
        if p.get('alignment', {}).get('rework_score') is not None
    ]
    latencies = [
        p['alignment']['latency_ms']
        for p in cycle_pairs
        if p.get('alignment', {}).get('latency_ms')
    ]
    deletion_ratios = [
        p['user_intent']['deletion_ratio']
        for p in cycle_pairs
        if p.get('user_intent', {}).get('deletion_ratio') is not None
    ]
    physical_keystroke_rate = (
        sum(1 for p in cycle_pairs if p.get('alignment', {}).get('had_physical_keystroke'))
        / len(cycle_pairs) if cycle_pairs else 0
    )
    response_capture_rate = (
        sum(1 for p in cycle_pairs if p.get('alignment', {}).get('response_captured'))
        / len(cycle_pairs) if cycle_pairs else 0
    )

    # Intent classification distribution
    intents = {}
    for p in cycle_pairs:
        intent = p.get('user_intent', {}).get('classified_intent', 'unknown')
        intents[intent] = intents.get(intent, 0) + 1

    # Edit source distribution
    sources = {}
    for p in cycle_pairs:
        for src in p.get('copilot_intent', {}).get('edit_sources', ['unknown']):
            sources[src] = sources.get(src, 0) + 1

    # Files touched
    files = list({p.get('copilot_intent', {}).get('file', '') for p in cycle_pairs})
    completion_notes = [
        p.get('completion', {}).get('completion_note', '')
        for p in cycle_pairs
        if p.get('completion', {}).get('completion_note')
    ]
    work_notes = [
        p.get('completion', {}).get('work_note', '')
        for p in cycle_pairs
        if p.get('completion', {}).get('work_note')
    ]
    response_summaries = [
        p.get('completion', {}).get('response_summary', '')
        for p in cycle_pairs
        if p.get('completion', {}).get('response_summary')
    ]

    summary = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'cycle': 'push_summary',
        'pair_count': len(cycle_pairs),
        'metrics': {
            'avg_rework_score': round(sum(rework_scores) / len(rework_scores), 3) if rework_scores else None,
            'avg_latency_ms': round(sum(latencies) / len(latencies)) if latencies else None,
            'avg_deletion_ratio': round(sum(deletion_ratios) / len(deletion_ratios), 3) if deletion_ratios else None,
            'physical_keystroke_rate': round(physical_keystroke_rate, 3),
            'response_capture_rate': round(response_capture_rate, 3),
            'rework_scored_count': len(rework_scores),
        },
        'intent_distribution': intents,
        'edit_source_distribution': sources,
        'files_touched': files[:20],
        'completion_summary': {
            'recent_completion_notes': completion_notes[-5:],
            'response_samples': response_summaries[-3:],
            'top_work_notes': _top_counts(work_notes),
        },
    }

    # Merge push cycle data if available
    if cycle:
        summary['push_cycle'] = {
            'cycle_number': cycle.get('cycle_number'),
            'sync_score': cycle.get('sync', {}).get('score'),
            'prediction_f1': cycle.get('prediction_score', {}).get('avg_f1'),
            'predictions_fired': cycle.get('new_predictions', 0),
            'backward_runs': cycle.get('backward_runs', 0),
            'prompt_count': cycle.get('operator_signal', {}).get('prompt_count', 0),
            'response_count': len(response_summaries),
        }

    # Write
    out_path = logs / 'training_cycle_summaries.jsonl'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(summary) + '\n')

    return summary
