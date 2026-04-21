from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
import types
from pathlib import Path


def _bootstrap_src(root: Path) -> None:
    src_dir = root / 'src'
    sys.path.insert(0, str(root))
    if 'src' not in sys.modules:
        pkg = types.ModuleType('src')
        pkg.__path__ = [str(src_dir)]
        pkg.__package__ = 'src'
        sys.modules['src'] = pkg


def _load_modules(root: Path):
    _bootstrap_src(root)
    sim = importlib.import_module(
        'src.tc_sim_engine_seq001_v004_d0420__intent_simulation_on_typing_pause_lc_chore_pigeon_rename_cascade'
    )
    replay = importlib.import_module(
        'src.tc_sim_seq001_v002_d0420__replay_typed_sessions_through_the_lc_chore_pigeon_rename_cascade'
    )
    return sim, replay


def _collect_pauses(replay, session_count: int, pause_limit: int, min_len: int, pause_ms: int, context: str | None):
    sessions = replay.extract_sessions(min_buffer_len=min_len)
    if context:
        sessions = [session for session in sessions if session.context == context]
    sessions = sessions[-session_count:]

    pauses = []
    for session in sessions:
        pauses.extend(replay.find_pause_points(session, pause_ms=pause_ms, min_buffer_len=max(8, min_len // 2)))
    return pauses[-pause_limit:]


def benchmark(root: Path, session_count: int, pause_limit: int, min_len: int, pause_ms: int, context: str | None) -> dict:
    sim, replay = _load_modules(root)
    pauses = _collect_pauses(replay, session_count, pause_limit, min_len, pause_ms, context)
    if not pauses:
        return {
            'status': 'no_pauses',
            'session_count': session_count,
            'pause_limit': pause_limit,
            'context': context,
        }

    ctx = sim.load_context()
    profile = sim.load_profile()
    records = []
    variant_totals: dict[str, dict[str, float | int]] = {}

    for pause in pauses:
        variants = []
        for cfg in sim._SIM_CONFIGS:
            files = sim._select_files_for_sim(pause.buffer, ctx, cfg['profile_weight'])
            prompt = sim._build_sim_prompt(pause.buffer, ctx, files, cfg['name'], profile)
            t0 = time.time()
            text = sim._call_gemini_sim(prompt, cfg['temp'])
            latency_ms = int((time.time() - t0) * 1000)
            heur_score = sim._score_completion(text, pause.buffer, profile)
            actual = replay.score_prediction(pause, text)
            item = {
                'name': cfg['name'],
                'heuristic_score': heur_score,
                'actual_overlap': actual.word_overlap,
                'prefix_match_len': actual.prefix_match_len,
                'exact_match': actual.exact_match,
                'latency_ms': latency_ms,
                'files': [entry['name'] for entry in files],
                'prediction': (text or '')[:300],
                'actual_continuation': (actual.continuation_captured or '')[:300],
            }
            variants.append(item)

            totals = variant_totals.setdefault(cfg['name'], {
                'n': 0,
                'heuristic_score_sum': 0.0,
                'actual_overlap_sum': 0.0,
                'latency_sum_ms': 0.0,
                'heuristic_wins': 0,
                'actual_wins': 0,
            })
            totals['n'] += 1
            totals['heuristic_score_sum'] += heur_score
            totals['actual_overlap_sum'] += actual.word_overlap
            totals['latency_sum_ms'] += latency_ms

        heur_winner = max(variants, key=lambda variant: variant['heuristic_score'])
        actual_winner = max(variants, key=lambda variant: variant['actual_overlap'])
        variant_totals[heur_winner['name']]['heuristic_wins'] += 1
        variant_totals[actual_winner['name']]['actual_wins'] += 1

        records.append({
            'buffer_tail': pause.buffer[-140:],
            'heuristic_winner': heur_winner['name'],
            'heuristic_winner_overlap': heur_winner['actual_overlap'],
            'actual_best_variant': actual_winner['name'],
            'actual_best_overlap': actual_winner['actual_overlap'],
            'winner_match': heur_winner['name'] == actual_winner['name'],
            'variants': variants,
        })

    summary = {
        'status': 'ok',
        'pause_points_tested': len(records),
        'session_count': session_count,
        'pause_limit': pause_limit,
        'pause_ms': pause_ms,
        'context': context,
        'winner_match_rate': round(sum(1 for record in records if record['winner_match']) / len(records), 3),
        'avg_heuristic_winner_overlap': round(sum(record['heuristic_winner_overlap'] for record in records) / len(records), 3),
        'avg_actual_best_overlap': round(sum(record['actual_best_overlap'] for record in records) / len(records), 3),
        'variants': {},
        'samples': records[:3],
        'all_records': records,
    }

    for name, totals in variant_totals.items():
        count = max(1, int(totals['n']))
        summary['variants'][name] = {
            'avg_heuristic_score': round(float(totals['heuristic_score_sum']) / count, 3),
            'avg_actual_overlap': round(float(totals['actual_overlap_sum']) / count, 3),
            'avg_latency_ms': round(float(totals['latency_sum_ms']) / count, 1),
            'heuristic_wins': int(totals['heuristic_wins']),
            'actual_wins': int(totals['actual_wins']),
        }

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description='Benchmark tc_sim_engine against real pause continuations.')
    parser.add_argument('--sessions', type=int, default=6, help='number of recent sessions to inspect')
    parser.add_argument('--pauses', type=int, default=6, help='maximum recent pause points to benchmark')
    parser.add_argument('--min-len', type=int, default=12, help='minimum session buffer length')
    parser.add_argument('--pause-ms', type=int, default=1200, help='pause threshold in ms')
    parser.add_argument('--context', type=str, default=None, help='optional context filter, e.g. editor or chat')
    parser.add_argument('--output', type=str, default='logs/tc_sim_engine_quality.json', help='where to write the benchmark JSON')
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    report = benchmark(root, args.sessions, args.pauses, args.min_len, args.pause_ms, args.context)

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({
        'status': report['status'],
        'pause_points_tested': report.get('pause_points_tested', 0),
        'winner_match_rate': report.get('winner_match_rate'),
        'avg_heuristic_winner_overlap': report.get('avg_heuristic_winner_overlap'),
        'avg_actual_best_overlap': report.get('avg_actual_best_overlap'),
        'variants': report.get('variants', {}),
        'output': str(out_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())