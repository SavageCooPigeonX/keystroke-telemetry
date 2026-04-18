"""净拆f_rcs_s010_v006_d0322_译测编深划_λW_main_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 29 lines | ~267 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, sys, argparse, shutil, traceback, importlib.util, glob as _glob

def main():
    parser = argparse.ArgumentParser(description="Pigeon Compiler — Clean Split")
    parser.add_argument("target", nargs="?",
                        help="Source file (relative to codebase_auditor/)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--name", help="Target folder name override")
    args = parser.parse_args()

    ca = PROJECT_ROOT / "codebase_auditor"
    targets = []
    if args.all:
        targets = [(ca / "folder_auditor.py", "folder_auditor"),
                   (ca / "master_auditor.py", "master_auditor")]
    elif args.target:
        t = ca / args.target
        targets = [(t, args.name or t.stem)]
    else:
        parser.print_help()
        return

    for src, name in targets:
        try:
            run(src, name)
        except Exception as e:
            print(f"FATAL: {e}")
            traceback.print_exc()
