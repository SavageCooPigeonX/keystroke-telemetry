"""批编f_rbc_s015_v002_d0328_织谱建验_λR_main_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 20 lines | ~207 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import sys, argparse, traceback, re

def main():
    parser = argparse.ArgumentParser(
        description="Pigeon Batch Compiler — compile entire codebase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan and plan but don't compile")
    parser.add_argument("--include-compiler", action="store_true",
                        help="Also compile pigeon_compiler's own oversized files")
    parser.add_argument("--root", default=str(PROJECT_ROOT),
                        help="Project root directory")
    args = parser.parse_args()

    batch_compile(
        root=Path(args.root),
        dry_run=args.dry_run,
        include_compiler=args.include_compiler,
    )
