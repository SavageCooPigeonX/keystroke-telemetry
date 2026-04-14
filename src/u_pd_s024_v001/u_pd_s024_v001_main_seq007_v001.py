"""u_pd_s024_v001_main_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 23 lines | ~161 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import sys

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
