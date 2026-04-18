"""tc_sim_seq001_v001_narrate_chapters_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 65 lines | ~659 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re
import sys
import time

def _print_narrate_header():
    print()
    print('═' * 70)
    print('  WHAT THIS SYSTEM IS AND WHAT IT KNOWS ABOUT YOU')
    print('  (the files are talking now)')
    print('═' * 70)


def _print_narrate_chapter1():
    print('\n┌─── CHAPTER 1: WHAT AM I? ───┐\n')
    print('  i watch you type.')
    print()
    print('  every keystroke, every pause, every backspace, every word you')
    print('  delete before hitting enter — i see all of it. when you stop')
    print('  typing for a second or two, i try to guess what you\'re about')
    print('  to say next. i use gemini (a fast AI model) to make that guess.')
    print()
    print('  the goal: finish your thought before you finish typing it.')
    print('  a popup appears with what i think you\'ll say next.')
    print()
    print('  right now i\'m not great at it. but i\'m learning.')


def _print_narrate_chapter5(ctx):
    print('┌─── CHAPTER 5: SO WHAT DOES ALL THIS MEAN? ───┐\n')
    print('  you type, pause, delete, rewrite, and eventually hit enter.')
    print('  this system sees ALL of that. it builds a model of how you think.')
    print()
    print('  "organism health" = how well the CODEBASE is doing.')
    print('  "operator state"  = how well YOU are doing.')
    print()
    print('  when the organism is sick (lots of bugs, high entropy, dead code),')
    print('  the AI should be more careful — more precise, less creative.')
    print('  when you\'re frustrated (high deletion, lots of rewrites),')
    print('  the AI should be more direct — shorter answers, less fluff.')
    print()
    print('  the thought completer uses ALL of this to guess your next words.')
    print('  your cognitive state, the codebase health, what files are hot,')
    print('  what you deleted, what you almost said — it\'s all signal.')
    print()

    fprofs = ctx.get('file_profiles', [])
    if fprofs:
        print('  some files even have personalities:')
        for fp in fprofs[:4]:
            fears = ', '.join(fp['fears'][:2]) if fp['fears'] else 'nothing'
            print(f'    {fp["mod"]}: {fp["personality"]} '
                  f'(hesitation={fp["hes"]:.0%}, fears: {fears})')
        print()

    print('  that\'s it. that\'s the system. it watches you type and tries')
    print('  to read your mind. sometimes it works. usually it doesn\'t.')
    print('  but it\'s getting better, one sim run at a time.')


def _print_narrate_footer():
    print('\n' + '═' * 70)
    print('  END OF NARRATION')
    print('═' * 70)
