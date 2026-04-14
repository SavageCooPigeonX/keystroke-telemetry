"""tc_sim_main_seq027_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 027 | VER: v001 | 138 lines | ~1,693 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from src.tc_constants import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import json
import os
import re
import time

def main():
    import argparse
    p = argparse.ArgumentParser(description='thought completer sim — replay & score')
    p.add_argument('--n', type=int, default=5, help='number of recent sessions')
    p.add_argument('--live', action='store_true', help='call Gemini (costs API)')
    p.add_argument('--session', type=int, default=None, help='specific session index')
    p.add_argument('--min-len', type=int, default=8, help='min buffer length')
    p.add_argument('--pause-ms', type=int, default=DEFAULT_PAUSE_MS, help='pause threshold')
    p.add_argument('--export', type=str, default=None, help='export path (.jsonl)')
    p.add_argument('--context', type=str, default=None, help='filter by context (editor/chat)')
    p.add_argument('--transcript', action='store_true', help='comedy narrative transcript')
    p.add_argument('--fix', action='store_true', help='diagnose + apply fixes from sim data')
    p.add_argument('--fix-dry', action='store_true', help='diagnose only, show what would fix')
    p.add_argument('--narrate', action='store_true', help='plain english explanation of everything')
    p.add_argument('--historical', action='store_true', help='use historical context for each pause (fixes context mismatch bug)')
    args = p.parse_args()

    print(f'[sim] extracting sessions from {KEYSTROKE_LOG.name}...')
    sessions = extract_sessions(min_buffer_len=args.min_len)
    print(f'[sim] found {len(sessions)} sessions (min {args.min_len} chars)')

    if args.context:
        sessions = [s for s in sessions if s.context == args.context]
        print(f'[sim] filtered to {len(sessions)} {args.context} sessions')

    if args.session is not None:
        sessions = [s for s in sessions if s.index == args.session]
        if not sessions:
            print(f'[sim] session {args.session} not found')
            return
    else:
        sessions = sessions[-args.n:]

    all_results: list[SimResult] = []

    for sess in sessions:
        pauses = find_pause_points(sess, pause_ms=args.pause_ms)
        if not args.transcript:
            _print_session(sess, pauses)

        if args.live and pauses:
            for i, pause in enumerate(pauses):
                try:
                    result = replay_pause_live(pause, use_historical_ctx=args.historical)
                    if not args.transcript:
                        _print_result(result, i + 1)
                    all_results.append(result)
                except Exception as e:
                    print(f'  pause {i+1} error: {e}')
                # Rate limit: 200ms between API calls
                if i < len(pauses) - 1:
                    time.sleep(0.2)

    # Transcript mode — comedy narrative
    if args.transcript:
        print_transcript(sessions, all_results if all_results else None)

    # Narrate mode — plain english explanation
    if args.narrate:
        print_narrate(sessions, all_results if all_results else None)

    if all_results:
        if not args.transcript:
            _print_summary(all_results)
        if args.export:
            export_results(all_results, Path(args.export))
        # Update sim memory — each file learns
        mem = update_sim_memory(all_results)
        file_count = len(mem.get('files', {}))
        print(f'[sim-memory] updated — {file_count} files tracked, '
              f'run #{mem.get("runs", 0)}')

    # Fix mode — diagnose and patch
    if args.fix or args.fix_dry:
        # Load previous results if we didn't just run live
        if not all_results:
            result_path = ROOT / 'logs' / 'sim_results.jsonl'
            if result_path.exists():
                print(f'[fix] loading previous results from {result_path.name}...')
                with open(result_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                d = json.loads(line)
                                pp = PausePoint(ts=0, buffer=d['buffer'],
                                                pause_ms=d.get('pause_ms', 0),
                                                buffer_after='',
                                                final_text=d.get('final_text', ''),
                                                position_pct=d.get('position_pct', 0))
                                sr = SimResult(pause=pp,
                                               prediction=d.get('prediction', ''),
                                               word_overlap=d.get('word_overlap', 0),
                                               prefix_match_len=d.get('prefix_match', 0),
                                               exact_match=d.get('exact', False),
                                               latency_ms=d.get('latency_ms', 0),
                                               context_files=d.get('context_files', []))
                                all_results.append(sr)
                            except Exception:
                                pass
                print(f'[fix] loaded {len(all_results)} previous results')

        if not all_results:
            print('[fix] no results to analyze — run with --live first')
            return

        bugs = diagnose_from_results(all_results)
        mem = _load_sim_memory()
        if not bugs:
            print('[fix] no bugs found — predictions are... fine? somehow?')
        else:
            print(f'\n[fix] {len(bugs)} bug(s) diagnosed:\n')
            for bug in bugs:
                sev = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(
                    bug['severity'], '⚪')
                print(f'  {sev} [{bug["id"]}] {bug["desc"]}')
                print(f'     file: {bug["file"]}')
                record_bug_found(mem, bug['id'], bug['desc'], bug['file'])
                result = apply_fix(bug, dry=args.fix_dry)
                prefix = 'DRY' if args.fix_dry else 'FIX'
                print(f'     {prefix}: {result}')
                if not args.fix_dry and 'PATCHED' in result:
                    record_bug_fixed(mem, bug['id'], result)
                print()

    if not args.live and not args.fix and not args.fix_dry:
        total_pauses = sum(len(find_pause_points(s, args.pause_ms)) for s in sessions)
        print(f'\n[sim] dry run complete — {total_pauses} pause points found')
        print(f'[sim] add --live to replay through Gemini and score accuracy')
        print(f'[sim] add --transcript for the comedy version')
        print(f'[sim] add --fix to diagnose and patch bugs from sim data')
