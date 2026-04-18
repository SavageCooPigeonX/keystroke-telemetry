"""tc_sim_seq001_v001_narrate_main_seq023_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 023 | VER: v001 | 18 lines | ~157 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import sys

def print_narrate(sessions: list[TypingSession],
                  results: list[SimResult] | None = None):
    """The system explains itself to you. Plain english, no jargon."""
    ctx = _narrate_context_signals()
    mem = _narrate_sim_memory()
    profile = _narrate_profile()

    _print_narrate_header()
    _print_narrate_chapter1()
    _print_narrate_chapter2(ctx, profile)
    _print_narrate_chapter3(ctx)
    _print_narrate_chapter4(sessions, results, mem)
    _print_narrate_chapter5(ctx)
    _print_narrate_footer()
