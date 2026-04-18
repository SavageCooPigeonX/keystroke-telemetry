"""u_pj_s019_v003_d0404_λNU_βoc_running_stats_decomposed_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 67 lines | ~701 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .p_u_pj_s001_v001 import JOURNAL_PATH
from .p_upsvdλβmh_s005_v001 import _is_operator_entry

def _running_stats(root: Path) -> dict:
    """Compute running session stats from existing journal entries + baselines."""
    p = root / JOURNAL_PATH
    if not p.exists():
        return {}
    try:
        entries = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    except Exception:
        return {}
    entries = [entry for entry in entries if _is_operator_entry(entry)]
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
    # Load real state distribution + baselines from operator_profile.md
    # (prompt_journal entries never receive classify results, so their
    #  cognitive_state is always '?' / 'unknown' — useless for stats)
    state_dist = {}
    dominant_state = 'unknown'
    baselines = {}
    try:
        import importlib.util
        matches = sorted(root.glob('src/控w_ops_s008*.py'))
        if matches:
            spec = importlib.util.spec_from_file_location('_os', matches[-1])
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                op_path = root / 'operator_profile.md'
                if op_path.exists():
                    stats = mod.OperatorStats(str(op_path))
                    baselines = mod.compute_baselines(stats._history)
                    from collections import Counter
                    real_states = [r['state'] for r in stats._history if 'state' in r]
                    state_dist = dict(Counter(real_states).most_common(5))
                    if state_dist:
                        dominant_state = max(state_dist, key=state_dist.get)
    except Exception:
        pass

    # Fallback: if operator_profile gave nothing, count from journal entries
    if not state_dist:
        from collections import Counter
        states = [e.get('cognitive_state', 'unknown') for e in entries]
        state_dist = dict(Counter(states).most_common(5))

    return {
        'total_prompts': n,
        'avg_wpm':       round(sum(wpms) / len(wpms), 1) if wpms else None,
        'avg_del_ratio': round(sum(dels) / len(dels), 3) if dels else None,
        'dominant_state': dominant_state,
        'state_distribution': state_dist,
        'baselines': baselines if baselines else None,
    }
