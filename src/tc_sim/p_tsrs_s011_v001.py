"""tc_sim_seq001_v001_report_summary_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 33 lines | ~369 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

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
