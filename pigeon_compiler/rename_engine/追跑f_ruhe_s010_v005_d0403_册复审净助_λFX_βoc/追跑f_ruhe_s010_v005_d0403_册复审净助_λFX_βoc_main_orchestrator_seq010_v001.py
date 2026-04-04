"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_main_orchestrator_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Pigeon Compiler — Self-Healing Pipeline')
    parser.add_argument('root', nargs='?', default='.',
                        help='Project root directory')
    parser.add_argument('--execute', action='store_true',
                        help='Actually apply renames + write manifests')
    parser.add_argument('--manifests-only', action='store_true',
                        help='Only rebuild MANIFEST.md files (skip rename)')
    parser.add_argument('--skip-rename', action='store_true',
                        help='Skip file renaming, still do manifests + compliance')
    parser.add_argument('--auto-commit', action='store_true',
                        help='Automatically git commit changes')
    parser.add_argument('--commit-message', type=str,
                        default='chore(pigeon): auto-heal manifests + compliance',
                        help='Commit message for auto-commit')
    parser.add_argument('--intent', type=str, default='heal_pipeline',
                        help='Intent slug for this mutation cycle')
    args = parser.parse_args()

    report = run_heal_pipeline(
        root=args.root,
        execute=args.execute,
        manifests_only=args.manifests_only,
        skip_rename=args.skip_rename,
        intent=args.intent,
    )

    print()
    print(format_report(report))

    if args.auto_commit and args.execute:
        root = Path(args.root).resolve()
        git_commit_changes(root, args.commit_message)

    if not report.get('success'):
        sys.exit(1)
