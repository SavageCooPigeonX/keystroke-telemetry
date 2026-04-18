"""tc_sim_seq001_v001_narrate_chapter3_seq021_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 021 | VER: v001 | 64 lines | ~656 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re
import sys

def _print_narrate_chapter3(ctx):
    print('┌─── CHAPTER 3: WHAT IS "ORGANISM HEALTH"? ───┐\n')
    print('  the codebase — all these python files — is treated like a')
    print('  living organism. each file is an organ. here\'s the metaphor:')
    print()
    print('  • HEAT MAP      = which files are getting edited the most')
    print('                     (hot = lots of attention, cold = stable)')
    print('  • ENTROPY        = uncertainty. when a file gets edited, entropy')
    print('                     goes up (we\'re less sure it\'s correct).')
    print('                     when it\'s tested and confirmed, entropy goes down.')
    print('  • BUG DEMONS     = bugs that won\'t die. each bug gets a name and')
    print('                     a personality. if it keeps coming back, it\'s "chronic"')
    print('  • CLOTS          = dead code. files nobody imports. bloated modules.')
    print('                     like cholesterol in arteries — slows the whole thing.')
    print('  • COGNITIVE STATE = YOUR state. frustrated? focused? hesitant?')
    print('                     the system reads this from how you type.')
    print()

    org = ctx.get('organism_narrative', '')
    if org:
        print(f'  the organism\'s own words:')
        print(f'  "{org}"')
        print()

    heat = ctx.get('heat_map', [])
    if heat:
        print('  right now, the hottest files (most actively edited):')
        for h in heat[:5]:
            bar = '🔥' * max(1, min(5, int(h['heat'] * 5)))
            print(f'    {h["mod"]:35s} {bar} (heat={h["heat"]:.2f})')
        print()

    ent = ctx.get('entropy', {})
    if ent:
        g = ent.get('global', 0)
        hp = ent.get('high_pct', 0)
        hp_display = hp if hp <= 1 else hp / 100
        print(f'  global entropy: {g:.2f} (0=certain, 1=chaos)')
        print(f'  {hp_display:.0%} of modules are high-entropy (uncertain)')
        hotspots = ent.get('hotspots', [])
        if hotspots:
            print('  most uncertain modules:')
            for h in hotspots[:4]:
                print(f'    {h["mod"]:35s} H={h["H"]:.3f}')
        print()

    bugs = ctx.get('bug_demons', [])
    if bugs:
        print('  active bug demons:')
        for b in bugs[:5]:
            print(f'    🐛 {b["demon"]} — haunting {b["host"]}')
        print()

    crits = ctx.get('critical_bugs', [])
    if crits:
        print('  critical issues:')
        for c in crits[:4]:
            print(f'    🔴 {c["type"]} in {c["file"]}')
        print()
