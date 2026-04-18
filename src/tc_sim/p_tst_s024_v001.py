"""tc_sim_seq001_v001_transcript_seq024_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v001 | 156 lines | ~1,561 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from src.tc_constants_seq001_v001_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import json
import os
import re

def _load_journal_arc(n: int = 10) -> list[dict]:
    """Load last n prompt journal entries for narrative context."""
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return []
    entries = []
    with open(journal, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries[-n:]


def print_transcript(sessions: list[TypingSession],
                     results: list[SimResult] | None = None):
    """Print the sim as a comedy narrative transcript."""
    journal = _load_journal_arc(15)

    print('\n' + '═' * 70)
    print('  THE THOUGHT COMPLETER TAPES')
    print('  a tragicomedy in keystrokes')
    print('═' * 70)

    # Act 1 — the journal arc (what the operator was going through)
    if journal:
        print('\n╔══ ACT 1: THE OPERATOR\'S DESCENT ══╗\n')
        for e in journal[-8:]:
            n = e.get('session_n', '?')
            cog = e.get('cognitive_state', 'unknown')
            intent = e.get('intent', 'unknown')
            emoji = _COG_EMOJI.get(cog, '❓')
            msg = e.get('msg', '')[:70]
            dels = e.get('deleted_words', [])
            sig = e.get('signals', {})
            del_r = sig.get('deletion_ratio', 0)

            print(f'  {emoji} prompt #{n} — {intent}, {cog}')
            print(f'     "{msg}"')
            if dels:
                print(f'     [whispered then swallowed: "{", ".join(dels)}"]')
            if del_r > 0.3:
                print(f'     [REWROTE {del_r:.0%} of this — the inner editor was fighting]')
            print()

    # Act 2 — the sessions themselves
    print('╔══ ACT 2: THE REPLAY ══╗\n')

    for sess in sessions:
        del_pct = f'{sess.deletion_ratio:.0%}'
        dur_s = sess.duration_ms / 1000
        drama = ''
        if sess.deletion_ratio > 0.3:
            drama = ' [THE BACKSPACE WAS DOING OVERTIME]'
        elif dur_s > 600:
            drama = f' [sat there for {dur_s/60:.0f} minutes]'
        elif sess.keystroke_count < 15:
            drama = ' [barely typed anything]'

        print(f'  ┌─ SESSION {sess.index} ─{drama}')
        print(f'  │ {sess.keystroke_count} keys, {del_pct} deleted, '
              f'{dur_s:.0f}s in the chair')
        print(f'  │ final: "{sess.final_buffer[:65]}"')

        pauses = find_pause_points(sess)
        if not pauses:
            print(f'  │ (typed without pausing. a rare confident moment.)')
        else:
            for i, p in enumerate(pauses):
                pause_s = p.pause_ms / 1000
                cont = _extract_continuation(p.buffer, p.final_text)
                if pause_s > 30:
                    pause_note = f'stared at screen for {pause_s:.0f}s'
                elif pause_s > 5:
                    pause_note = f'{pause_s:.1f}s pause (thinking)'
                else:
                    pause_note = f'{pause_s:.1f}s hesitation'
                print(f'  │')
                print(f'  │  ⏸  {pause_note} at "{p.buffer[-40:]}"')
                if cont:
                    print(f'  │  ▶  then typed: "{cont[:50]}"')
        print(f'  └─────\n')

    # Act 3 — the predictions (if we have live results)
    if results:
        print('╔══ ACT 3: THE AI TRIES TO READ MINDS ══╗\n')
        good = [r for r in results if r.word_overlap > 0.15]
        bad = [r for r in results if r.word_overlap < 0.05]
        ok = [r for r in results if 0.05 <= r.word_overlap <= 0.15]

        for r in results:
            buf_short = r.pause.buffer[-45:]
            pred_short = r.prediction[:50]
            actual_short = r.continuation_captured[:50]
            ov = r.word_overlap

            if ov > 0.2:
                verdict = '✨ ALMOST READ THEIR MIND'
            elif ov > 0.1:
                verdict = '🤷 wrong words, right vibe'
            elif ov > 0.03:
                verdict = '😬 technically english'
            else:
                verdict = '💀 completely wrong planet'

            # duplicate context file comedy
            unique_ctx = list(dict.fromkeys(r.context_files))
            if len(r.context_files) != len(unique_ctx):
                ctx_note = f' [selected {r.context_files[0]} TWICE — thats the bug]'
            elif len(set(r.context_files)) == 1 and len(r.context_files) > 1:
                ctx_note = f' [all {len(r.context_files)} context files are the SAME file]'
            else:
                ctx_note = ''

            print(f'  operator: "...{buf_short}"')
            print(f'  AI said:  "{pred_short}"')
            print(f'  reality:  "{actual_short}"')
            print(f'  {verdict} ({ov:.0%} overlap, {r.latency_ms}ms){ctx_note}')
            print()

        # Epilogue
        avg_ov = sum(r.word_overlap for r in results) / len(results) if results else 0
        print('╔══ EPILOGUE ══╗\n')
        print(f'  {len(results)} predictions attempted')
        print(f'  {len(good)} had a clue, {len(ok)} were vibing, {len(bad)} were fiction')
        print(f'  average overlap: {avg_ov:.1%}')
        if avg_ov < 0.1:
            print(f'  verdict: the AI is writing fanfiction, not predictions')
        elif avg_ov < 0.2:
            print(f'  verdict: occasionally psychic, mostly just chatty')
        else:
            print(f'  verdict: getting there — the signal is real')

        # The bugs found
        ctx_counts = {}
        for r in results:
            for f in r.context_files:
                ctx_counts[f] = ctx_counts.get(f, 0) + 1
        if ctx_counts:
            top = sorted(ctx_counts.items(), key=lambda x: x[1], reverse=True)
            if top[0][1] > len(results) * 0.5:
                print(f'\n  🐛 BUG SPOTTED: context agent selected "{top[0][0]}" '
                      f'in {top[0][1]}/{len(results)} predictions')
                print(f'     thats not context selection — thats a fixation')

    print('\n' + '═' * 70)
    print('  END OF TAPES')
    print('═' * 70)
