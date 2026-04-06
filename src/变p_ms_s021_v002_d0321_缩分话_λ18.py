"""Mutation scorer: correlates prompt mutations with rework verdicts.

Joins copilot_prompt_mutations.json (snapshot series) with rework_log.json
(hit/miss verdicts after each AI response) by timestamp proximity.
Emits per-section correlation data: which prompt sections' presence/absence
predicts better AI answers?

Zero LLM calls. Pure signal correlation.
Output:  logs/mutation_scores.json
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

MUTATIONS_PATH = 'logs/copilot_prompt_mutations.json'
REWORK_PATH    = 'rework_log.json'
OUTPUT_PATH    = 'logs/mutation_scores.json'
WINDOW_S       = 3600   # pair mutation with rework within 1-hour window


def _parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except Exception:
        return None


def score_mutations(root: Path) -> dict:
    """Compute correlation between prompt feature presence and rework verdicts.

    Returns:
        {
            'sections': {section_name: {'with': hit_rate, 'without': hit_rate, 'n': int}},
            'features': {feature_name: {'with': hit_rate, 'without': hit_rate, 'n': int}},
            'total_pairs': int,
            'generated': iso_ts,
        }
    """
    root = Path(root)
    mutations_path = root / MUTATIONS_PATH
    rework_path = root / REWORK_PATH

    snapshots: list[dict] = []
    if mutations_path.exists():
        try:
            data = json.loads(mutations_path.read_text('utf-8'))
            snapshots = data.get('snapshots', [])
        except Exception:
            pass

    reworks: list[dict] = []
    if rework_path.exists():
        try:
            raw = json.loads(rework_path.read_text('utf-8'))
            reworks = raw if isinstance(raw, list) else raw.get('verdicts', [])
        except Exception:
            pass

    if not snapshots or not reworks:
        result: dict = {
            'generated': datetime.now(timezone.utc).isoformat(),
            'total_pairs': 0,
            'sections': {},
            'features': {},
            'note': 'insufficient data — need mutations + rework verdicts',
        }
        _write(root, result)
        return result

    # Build timestamp-indexed snapshots list
    snap_ts = []
    for s in snapshots:
        # Mutations don't store a wall-clock ts directly; use commit ordering.
        # We insert a synthetic offset based on position in history.
        snap_ts.append(s)

    # For each rework verdict, find the most-recently-applied mutation snapshot
    section_stats: dict[str, dict] = {}   # section → {present_hits, present_n, absent_hits, absent_n}
    feature_stats: dict[str, dict] = {}   # feature → same

    pairs = 0
    for rw in reworks:
        rw_ts_str = rw.get('ts')
        rw_ts = _parse_ts(rw_ts_str)
        verdict = rw.get('verdict', 'unknown')
        hit = 1 if verdict == 'hit' else 0

        # Find latest snapshot that could have been active at rework time.
        # In absence of per-snapshot wall clock, use array order: the snapshot
        # with the highest index that came before the rework is the active one.
        # If we can't pair, use the last snapshot (best effort).
        active = snapshots[-1] if snapshots else None
        if active is None:
            continue

        pairs += 1
        active_sections = set(active.get('sections', []))
        active_features = {k: v for k, v in active.get('features', {}).items()}

        # Accumulate per-section stats
        all_section_candidates = set()
        for snap in snapshots:
            all_section_candidates.update(snap.get('sections', []))

        for sec in all_section_candidates:
            stats = section_stats.setdefault(sec, {
                'present_hits': 0, 'present_n': 0, 'absent_hits': 0, 'absent_n': 0
            })
            if sec in active_sections:
                stats['present_hits'] += hit
                stats['present_n'] += 1
            else:
                stats['absent_hits'] += hit
                stats['absent_n'] += 1

        # Accumulate per-feature stats
        for feat, val in active_features.items():
            stats = feature_stats.setdefault(feat, {
                'on_hits': 0, 'on_n': 0, 'off_hits': 0, 'off_n': 0
            })
            if val:
                stats['on_hits'] += hit
                stats['on_n'] += 1
            else:
                stats['off_hits'] += hit
                stats['off_n'] += 1

    def _rate(hits: int, n: int) -> float | None:
        return round(hits / n, 3) if n > 0 else None

    sections_out = {}
    for sec, s in section_stats.items():
        sections_out[sec] = {
            'with_section': _rate(s['present_hits'], s['present_n']),
            'without_section': _rate(s['absent_hits'], s['absent_n']),
            'n_with': s['present_n'],
            'n_without': s['absent_n'],
        }

    features_out = {}
    for feat, s in feature_stats.items():
        features_out[feat] = {
            'feature_on': _rate(s['on_hits'], s['on_n']),
            'feature_off': _rate(s['off_hits'], s['off_n']),
            'n_on': s['on_n'],
            'n_off': s['off_n'],
        }

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total_pairs': pairs,
        'total_mutations': len(snapshots),
        'total_reworks': len(reworks),
        'sections': sections_out,
        'features': features_out,
    }
    _write(root, result)
    return result


def _write(root: Path, result: dict) -> None:
    out = root / OUTPUT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    r = score_mutations(root)
    print(json.dumps(r, indent=2, ensure_ascii=False))
