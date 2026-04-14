"""tc_sim_report_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 67 lines | ~713 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re

def _print_session(sess: TypingSession, pauses: list[PausePoint]):
    """Print a compact session summary."""
    del_pct = f'{sess.deletion_ratio:.0%}'
    print(f'\n{"="*70}')
    print(f'SESSION {sess.index} | {sess.context} | '
          f'{sess.keystroke_count} keys | del={del_pct} | '
          f'{sess.duration_ms}ms')
    print(f'  final: "{sess.final_buffer[:70]}"')
    if not pauses:
        print(f'  (no pauses >= threshold)')
    for i, p in enumerate(pauses):
        cont = _extract_continuation(p.buffer, p.final_text)
        print(f'  pause {i+1}: {p.pause_ms}ms @ {p.position_pct:.0%} '
              f'| buf="{p.buffer[:50]}"')
        if cont:
            print(f'    → typed after: "{cont[:60]}"')


def _print_result(result: SimResult, idx: int):
    """Print one sim result with accuracy."""
    p = result.pause
    print(f'\n  ── pause {idx} ({p.pause_ms}ms @ {p.position_pct:.0%}) ──')
    print(f'  buffer:     "{p.buffer[:60]}"')
    print(f'  predicted:  "{result.prediction[:60]}"')
    print(f'  actual:     "{result.continuation_captured[:60]}"')
    print(f'  overlap:    {result.word_overlap:.0%} | '
          f'prefix: {result.prefix_match_len} chars | '
          f'exact: {result.exact_match} | '
          f'{result.latency_ms}ms')
    if result.context_files:
        print(f'  files:      {", ".join(result.context_files[:4])}')


def _print_summary(results: list[SimResult]):
    """Print aggregate accuracy stats."""
    if not results:
        print('\nno results to summarize')
        return
    overlaps = [r.word_overlap for r in results]
    latencies = [r.latency_ms for r in results if r.latency_ms > 0]
    prefixes = [r.prefix_match_len for r in results]
    exact = sum(1 for r in results if r.exact_match)

    print(f'\n{"="*70}')
    print(f'SIMULATION SUMMARY — {len(results)} pause points replayed')
    print(f'  word overlap:   avg={sum(overlaps)/len(overlaps):.1%} '
          f'| max={max(overlaps):.1%} | min={min(overlaps):.1%}')
    print(f'  prefix match:   avg={sum(prefixes)/len(prefixes):.1f} chars '
          f'| max={max(prefixes)}')
    print(f'  exact matches:  {exact}/{len(results)} ({exact/len(results):.0%})')
    if latencies:
        print(f'  latency:        avg={sum(latencies)/len(latencies):.0f}ms '
              f'| max={max(latencies)}ms | min={min(latencies)}ms')

    # Best and worst predictions
    by_overlap = sorted(results, key=lambda r: r.word_overlap, reverse=True)
    if by_overlap:
        best = by_overlap[0]
        print(f'\n  BEST:  "{best.pause.buffer[:40]}" → '
              f'overlap={best.word_overlap:.0%}')
        worst = by_overlap[-1]
        print(f'  WORST: "{worst.pause.buffer[:40]}" → '
              f'overlap={worst.word_overlap:.0%}')
