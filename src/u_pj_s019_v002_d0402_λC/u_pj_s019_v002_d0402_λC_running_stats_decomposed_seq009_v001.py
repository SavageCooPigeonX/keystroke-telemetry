"""u_pj_s019_v002_d0402_λC_running_stats_decomposed_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _running_stats(root: Path) -> dict:
    """Compute running session stats from existing journal entries + baselines."""
    p = root / JOURNAL_PATH
    if not p.exists():
        return {}
    try:
        entries = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    except Exception:
        return {}
    if not entries:
        return {}
    n = len(entries)
    # Running averages from entries that have signals
    wpms = [e['signals']['wpm'] for e in entries
             if 'signals' in e and 'wpm' in e.get('signals', {})
             and e['signals']['wpm'] <= 300]
    dels = [
        e['signals']['deletion_ratio']
        for e in entries
        if isinstance(e.get('signals'), dict) and 'deletion_ratio' in e['signals']
    ]
    states = [e.get('cognitive_state', 'unknown') for e in entries]
    from collections import Counter
    state_dist = dict(Counter(states).most_common(5))

    # Load self-calibration baselines from operator_stats
    baselines = {}
    try:
        import glob, importlib.util
        matches = sorted(root.glob('src/控w_ops_s008*.py'))
        if matches:
            spec = importlib.util.spec_from_file_location('_os', matches[-1])
            if spec is None or spec.loader is None:
                return {
                    'total_prompts': n,
                    'avg_wpm':       round(sum(wpms) / len(wpms), 1) if wpms else None,
                    'avg_del_ratio': round(sum(dels) / len(dels), 3) if dels else None,
                    'state_distribution': state_dist,
                    'baselines': None,
                }
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            op_path = root / 'operator_profile.md'
            if op_path.exists():
                stats = mod.OperatorStats(str(op_path))
                baselines = mod.compute_baselines(stats._history)
    except Exception:
        pass

    return {
        'total_prompts': n,
        'avg_wpm':       round(sum(wpms) / len(wpms), 1) if wpms else None,
        'avg_del_ratio': round(sum(dels) / len(dels), 3) if dels else None,
        'state_distribution': state_dist,
        'baselines': baselines if baselines else None,
    }
