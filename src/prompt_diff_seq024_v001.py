"""Prompt version diff CLI.

Usage:
    py -m src.prompt_diff_seq024_v001 [block_name] [N]

    block_name — section name substring to diff (default: show full section list)
    N          — number of recent snapshots to compare (default: 2, max: last N vs N-1)

Examples:
    py -m src.prompt_diff_seq024_v001                       # list all sections
    py -m src.prompt_diff_seq024_v001 "Module Map"          # diff last 2 snapshots of Module Map
    py -m src.prompt_diff_seq024_v001 features 5            # show feature evolution over last 5 snapshots

Output: colored unified diff to stdout (ANSI escape codes, stripped on non-TTY).
"""
# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v001 | ~110 lines
# DESC:   prompt_version_diff_cli
# INTENT: developer_tool
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
from __future__ import annotations
import difflib
import json
import sys
from pathlib import Path

MUTATIONS_PATH = 'logs/copilot_prompt_mutations.json'

_RED   = '\033[31m'
_GREEN = '\033[32m'
_CYAN  = '\033[36m'
_RESET = '\033[0m'


def _colorize(line: str, use_color: bool) -> str:
    if not use_color:
        return line
    if line.startswith('+') and not line.startswith('+++'):
        return _GREEN + line + _RESET
    if line.startswith('-') and not line.startswith('---'):
        return _RED + line + _RESET
    if line.startswith('@@'):
        return _CYAN + line + _RESET
    return line


def _load_snapshots(root: Path) -> list[dict]:
    p = root / MUTATIONS_PATH
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text('utf-8'))
        return data.get('snapshots', [])
    except Exception:
        return []


def _section_text(snap: dict, block: str) -> str:
    """Extract text representing `block` from a snapshot.
    block='features' → JSON dump of features dict.
    Otherwise → 'present' / 'absent' + snapshot metadata.
    """
    if block.lower() == 'features':
        feats = snap.get('features', {})
        return '\n'.join(f'  {k}: {v}' for k, v in sorted(feats.items()))
    sections = snap.get('sections', [])
    matched = [s for s in sections if block.lower() in s.lower()]
    if not matched:
        return f'(section not present in commit {snap.get("commit","?")})'
    # Represent as "section header + lines count" — we don't store per-section text
    meta = snap.get('commit', '?')[:7]
    return '\n'.join(f'  [{meta}] {s}  ({snap.get("lines","?")} total lines, {snap.get("bytes","?")} bytes)' for s in matched)


def list_sections(snapshots: list[dict]) -> None:
    print('Sections present across all snapshots:')
    all_sections: dict[str, int] = {}
    for snap in snapshots:
        for s in snap.get('sections', []):
            all_sections[s] = all_sections.get(s, 0) + 1
    for s, cnt in sorted(all_sections.items(), key=lambda x: -x[1]):
        print(f'  [{cnt:3d}x] {s}')
    print(f'\nTotal snapshots: {len(snapshots)}')
    print('Usage: py -m src.prompt_diff_seq024_v001 "<section name>" [N snapshots]')


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


def main() -> None:
    import os
    args = sys.argv[1:]
    root = Path('.')
    block = args[0] if args else None
    n = int(args[1]) if len(args) >= 2 else 2

    snapshots = _load_snapshots(root)
    if not snapshots:
        print(f'No snapshots found at {root / MUTATIONS_PATH}')
        sys.exit(1)

    use_color = sys.stdout.isatty() and os.name != 'nt' or os.environ.get('FORCE_COLOR')

    if block is None:
        list_sections(snapshots)
        return

    diff_block(snapshots, block, max(n, 2), bool(use_color))


if __name__ == '__main__':
    main()
