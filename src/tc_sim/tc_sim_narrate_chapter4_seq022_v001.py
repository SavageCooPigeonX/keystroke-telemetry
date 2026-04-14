"""tc_sim_narrate_chapter4_seq022_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 022 | VER: v001 | 94 lines | ~1,058 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re
import time

def _print_narrate_chapter4(sessions, results, mem):
    print('┌─── CHAPTER 4: WHAT I LEARNED FROM REPLAYING YOUR TYPING ───┐\n')

    total_sess = len(sessions)
    total_keys = sum(s.keystroke_count for s in sessions)
    total_bs = sum(s.backspace_count for s in sessions)
    total_pauses = sum(len(find_pause_points(s)) for s in sessions)

    print(f'  i replayed {total_sess} of your typing sessions.')
    print(f'  you pressed {total_keys} keys total. {total_bs} of those were backspace.')
    if total_keys > 0:
        print(f'  that\'s a {total_bs/total_keys:.0%} deletion rate.')
    print(f'  you paused long enough to trigger prediction {total_pauses} times.')
    print()

    if sessions:
        longest = max(sessions, key=lambda s: s.duration_ms)
        most_del = max(sessions, key=lambda s: s.deletion_ratio)
        print(f'  your longest session: #{longest.index} '
              f'({longest.duration_ms/1000:.0f}s) — "{longest.final_buffer[:50]}"')
        print(f'  your most edited session: #{most_del.index} '
              f'({most_del.deletion_ratio:.0%} deleted) — "{most_del.final_buffer[:50]}"')
        print()

    if results:
        overlaps = [r.word_overlap for r in results]
        avg_ov = sum(overlaps) / len(overlaps)
        best = max(results, key=lambda r: r.word_overlap)
        worst = min(results, key=lambda r: r.word_overlap)
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]

        print(f'  i made {len(results)} predictions. here\'s how they went:')
        print(f'    average accuracy (word overlap): {avg_ov:.1%}')
        print(f'    best:  {best.word_overlap:.0%} — "{best.pause.buffer[-40:]}"')
        print(f'    worst: {worst.word_overlap:.0%} — "{worst.pause.buffer[-40:]}"')
        if latencies:
            print(f'    average response time: {sum(latencies)/len(latencies):.0f}ms')
        print()

        good = sum(1 for r in results if r.word_overlap > 0.15)
        mid = sum(1 for r in results if 0.05 <= r.word_overlap <= 0.15)
        bad = sum(1 for r in results if r.word_overlap < 0.05)
        print(f'    {good} good guesses (>15% overlap)')
        print(f'    {mid} okay guesses (5-15%)')
        print(f'    {bad} bad guesses (<5%)')
        print()

        ctx_counts: dict[str, int] = {}
        for r in results:
            for f in r.context_files:
                ctx_counts[f] = ctx_counts.get(f, 0) + 1
        if ctx_counts:
            top_ctx = sorted(ctx_counts.items(), key=lambda x: -x[1])[:3]
            print('  the AI kept looking at these files for context:')
            for name, cnt in top_ctx:
                short = name.split('_seq')[0] if '_seq' in name else name
                print(f'    {short}: {cnt}x')
            print()
    else:
        print('  (no live predictions yet — run with --live to actually test)')
        print()

    files = mem.get('files', {})
    runs = mem.get('runs', 0)
    bugs_found = mem.get('bugs_found', [])
    bugs_fixed = mem.get('bugs_fixed', [])
    if files:
        print(f'  sim has run {runs} time(s). tracking {len(files)} files.')
        by_sel = sorted(files.items(), key=lambda x: -x[1].get('times_selected', 0))
        if by_sel:
            top = by_sel[0]
            short_name = top[0].split('_seq')[0] if '_seq' in top[0] else top[0]
            print(f'  most selected context file: {short_name} '
                  f'({top[1]["times_selected"]}x, {top[1]["avg_overlap"]:.1%} avg accuracy)')
            if top[1]['avg_overlap'] < 0.05:
                print(f'    ^ that file is selected a LOT but barely helps. '
                      f'context agent might be fixated.')
        print()

    if bugs_found:
        fixed_ids = {b['id'] for b in bugs_fixed}
        unfixed = [b for b in bugs_found if b['id'] not in fixed_ids and not b.get('fixed')]
        print(f'  bugs found by the sim: {len(bugs_found)}')
        print(f'  bugs fixed: {len(bugs_fixed)}')
        if unfixed:
            print(f'  still unfixed:')
            for b in unfixed[:3]:
                print(f'    - {b["desc"][:70]}')
        print()
