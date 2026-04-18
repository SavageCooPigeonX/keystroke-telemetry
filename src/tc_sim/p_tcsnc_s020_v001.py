"""tc_sim_seq001_v001_narrate_chapter2_seq020_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 020 | VER: v001 | 65 lines | ~656 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re
import time

def _print_narrate_chapter2(ctx, profile):
    print('\n┌─── CHAPTER 2: WHAT I KNOW ABOUT YOU ───┐\n')
    si = ctx.get('session_info', {})
    if si:
        cog = si.get('cognitive_state', 'unknown')
        intent = si.get('intent', 'unknown')
        sn = si.get('session_n', '?')
        print(f'  last time you talked to copilot, it was prompt #{sn}.')
        print(f'  your cognitive state was: {cog}')
        print(f'  your intent was: {intent}')
        print()

    op = ctx.get('operator_state', {})
    if op:
        dom = op.get('dominant', 'unknown')
        wpm = op.get('avg_wpm', 0)
        bl = op.get('baselines', {})
        bl_wpm = bl.get('avg_wpm', 0)
        bl_del = bl.get('avg_del', 0)
        print(f'  your dominant state across all sessions: {dom}')
        if bl_wpm:
            print(f'  you type at ~{bl_wpm:.0f} words per minute on average.')
        if bl_del:
            print(f'  you delete {bl_del:.0%} of what you type. that\'s your inner editor.')
        print()

    states = op.get('states', {}) if op else {}
    if states:
        total_states = sum(states.values())
        if total_states > 0:
            print('  how you\'ve been feeling (across all prompts):')
            for state, count in sorted(states.items(), key=lambda x: -x[1]):
                bar = '█' * max(1, int(count / total_states * 30))
                print(f'    {state:12s} {bar} ({count}x)')
            print()

    if profile and profile.get('samples', 0) > 0:
        v = profile.get('shards', {}).get('voice', {})
        if v.get('top_words'):
            top5 = list(v['top_words'].keys())[:7]
            print(f'  your most used words: {", ".join(top5)}')
        if v.get('catchphrases'):
            print(f'  your catchphrases: {", ".join(v["catchphrases"][:3])}')
        r = profile.get('shards', {}).get('rhythm', {})
        if r.get('avg_wpm'):
            print(f'  your measured typing speed: {r["avg_wpm"]:.0f} wpm')
        d = profile.get('shards', {}).get('deletions', {})
        if d.get('top_deleted_words'):
            tdw = list(d['top_deleted_words'].keys())[:5]
            print(f'  words you delete most: {", ".join(tdw)}')
        print()

    unsaid = ctx.get('unsaid_threads', [])
    if unsaid:
        real_unsaid = [u for u in unsaid if u.strip()]
        if real_unsaid:
            print('  things you typed then deleted (i still saw them):')
            for u in real_unsaid[:5]:
                print(f'    - "{u[:80]}"')
            print()
