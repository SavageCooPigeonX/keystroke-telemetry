"""tc_sim_seq001_v001_report_seq009_v001_print_session_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 20 lines | ~210 tokens
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
