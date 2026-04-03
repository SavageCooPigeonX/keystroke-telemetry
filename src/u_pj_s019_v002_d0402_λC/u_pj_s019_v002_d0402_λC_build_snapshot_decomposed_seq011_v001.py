"""u_pj_s019_v002_d0402_λC_build_snapshot_decomposed_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _build_snapshot(entry: dict) -> dict:
    running = entry.get('running', {})
    state_dist = running.get('state_distribution', {})
    rewrites = entry.get('rewrites', [])

    # Load fresh coaching directives from operator_coaching.md (< 2h old)
    root = entry.get('_root')
    coaching_bullets: list[str] = []
    if root:
        try:
            coaching_bullets = _load_fresh_coaching_bullets(root)
        except Exception:
            pass

    snapshot = {
        'schema': 'prompt_telemetry/latest/v1',
        'updated_at': entry['ts'],
        'latest_prompt': {
            'session_n': entry['session_n'],
            'ts': entry['ts'],
            'chars': entry['msg_len'],
            'preview': _trim_text(entry['msg'], 220),
            'intent': entry['intent'],
            'state': entry['cognitive_state'],
            'files_open': entry.get('files_open', [])[:6],
            'module_refs': sorted(entry.get('module_refs', []))[:8],
        },
        'signals': entry.get('signals', {}),
        'composition_binding': entry.get('composition_binding', {}),
        'deleted_words': entry.get('deleted_words', [])[:8],
        'rewrites': [
            {
                'old': _trim_text(str(r.get('old', '')), 80),
                'new': _trim_text(str(r.get('new', '')), 80),
            }
            for r in rewrites[:3]
        ],
        'task_queue': entry.get('task_queue', {}),
        'hot_modules': entry.get('hot_modules', []),
        'running_summary': {
            'total_prompts': running.get('total_prompts'),
            'avg_wpm': running.get('avg_wpm'),
            'avg_del_ratio': running.get('avg_del_ratio'),
            'dominant_state': _dominant_state(state_dist),
            'state_distribution': state_dist,
            'baselines': running.get('baselines'),
        },
    }
    if coaching_bullets:
        snapshot['coaching_directives'] = coaching_bullets

    # Predictive debug — surface likely next struggles
    if root:
        try:
            preds = _predict_next_issues(
                root, entry.get('intent', ''), entry.get('module_refs', []))
            if preds:
                snapshot['predicted_struggles'] = preds
        except Exception:
            pass

    return snapshot
