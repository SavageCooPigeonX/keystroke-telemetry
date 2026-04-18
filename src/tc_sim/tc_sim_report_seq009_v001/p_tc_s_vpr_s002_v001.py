"""tc_sim_seq001_v001_report_seq009_v001_print_result_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 17 lines | ~191 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re

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
