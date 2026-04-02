"""run_batch_compile_seq015_main_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
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


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
