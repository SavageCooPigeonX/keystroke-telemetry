"""u_pd_s024_v001_diff_block_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 21 lines | ~259 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import difflib

def diff_block(snapshots: list[dict], block: str, n: int, use_color: bool) -> None:
    tail = snapshots[-n:]
    if len(tail) < 2:
        print(f'Only {len(tail)} snapshot(s) available — need at least 2 to diff.')
        return
    for i in range(len(tail) - 1):
        a, b = tail[i], tail[i + 1]
        a_text = _section_text(a, block).splitlines(keepends=True)
        b_text = _section_text(b, block).splitlines(keepends=True)
        a_label = f'{a.get("commit","?")[:7]} — {a.get("message","")[:60]}'
        b_label = f'{b.get("commit","?")[:7]} — {b.get("message","")[:60]}'
        diffs = list(difflib.unified_diff(a_text, b_text, fromfile=a_label, tofile=b_label))
        if not diffs:
            print(f'No change in "{block}" between {a.get("commit","?")[:7]} and {b.get("commit","?")[:7]}')
        else:
            for line in diffs:
                print(_colorize(line.rstrip('\n'), use_color))
        print()
