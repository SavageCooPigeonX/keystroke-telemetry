"""run_rename_seq006_v001.py — Full rename pipeline runner.

Orchestrates: scan → plan → preview → rewrite imports → execute → validate.
Supports --dry-run, --folders, --rollback flags.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v005 | 143 lines | ~1,387 tokens
# DESC:   full_rename_pipeline_runner
# INTENT: add_chinese_glyph
# LAST:   2026-04-01 @ aa32a3f
# SESSIONS: 1
# ──────────────────────────────────────────────
import argparse
import json
import sys
from pathlib import Path

from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project
from pigeon_compiler.rename_engine.w_pl_s002_v005_d0401_册追跑谱桥_λA import build_rename_plan
from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename, rollback_rename
from pigeon_compiler.rename_engine.审p_va_s005_v005_d0403_踪稿析_λFX import validate_imports


def run_full_rename(root: str, folders: list = None,
                    dry_run: bool = True, version: str = '001') -> dict:
    """Execute full rename pipeline. Returns summary dict."""
    root = Path(root)
    report = {'stage': 'init', 'success': False}

    # Stage 1: Scan
    report['stage'] = 'scan'
    catalog = scan_project(root, folders)
    report['scan'] = catalog['stats']
    if catalog['stats']['non_compliant'] == 0:
        report['success'] = True
        report['message'] = 'All files already Pigeon Code compliant'
        return report

    # Stage 2: Plan
    report['stage'] = 'plan'
    plan = build_rename_plan(catalog, version, root=root)
    report['plan'] = plan['stats']
    report['renames'] = plan['renames']
    if not plan['renames']:
        report['success'] = True
        report['message'] = 'No renames needed'
        return report

    # Stage 3: Preview (always shown)
    report['stage'] = 'preview'
    report['preview'] = [
        f"  {r['old_path']} → {r['new_path']}"
        for r in plan['renames']
    ]

    if dry_run:
        report['success'] = True
        report['message'] = f"DRY RUN: {len(plan['renames'])} files would be renamed"
        return report

    # Stage 4: Rewrite imports
    report['stage'] = 'rewrite_imports'
    changes = rewrite_all_imports(root, plan['import_map'], dry_run=False)
    report['import_changes'] = len(changes)

    # Stage 5: Execute renames
    report['stage'] = 'execute'
    result = execute_rename(root, plan, dry_run=False)
    report['renamed'] = len(result['renamed'])
    report['errors'] = result['errors']
    report['rollback_log'] = result.get('rollback_log')

    if result['errors']:
        report['message'] = f"Completed with {len(result['errors'])} errors"
        report['success'] = False
        return report

    # Stage 6: Validate
    report['stage'] = 'validate'
    val = validate_imports(root)
    report['validation'] = {
        'valid': val['valid'],
        'broken_count': len(val['broken']),
        'broken': val['broken'][:10],  # first 10 only
    }
    report['success'] = val['valid']
    report['message'] = 'Rename complete — all imports valid' if val['valid'] \
        else f"Rename complete — {len(val['broken'])} broken imports"
    return report


def main():
    parser = argparse.ArgumentParser(description='Pigeon Compiler Rename Engine')
    parser.add_argument('root', nargs='?', default='.', help='Project root')
    parser.add_argument('--folders', nargs='*', help='Limit to specific folders')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Preview only (default)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform renames')
    parser.add_argument('--rollback', type=str,
                        help='Path to rollback log to undo renames')
    parser.add_argument('--version', default='001', help='Version suffix')
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.rollback:
        print(f'Rolling back from {args.rollback}...')
        result = rollback_rename(root, args.rollback)
        print(f"Rolled back {len(result['restored'])} files")
        if result['errors']:
            for e in result['errors']:
                print(f"  ERROR: {e}")
        return

    is_dry = not args.execute
    report = run_full_rename(str(root), args.folders, is_dry, args.version)

    print(f"\n=== Pigeon Rename Engine ===")
    print(f"Stage: {report['stage']}")
    if 'scan' in report:
        s = report['scan']
        print(f"Scanned: {s['total']} files, "
              f"{s['compliant']} compliant, {s['non_compliant']} non-compliant")
    if 'preview' in report:
        print(f"\nRenames ({len(report.get('renames', []))}):")
        for line in report['preview']:
            print(line)
    if 'import_changes' in report:
        print(f"\nImport rewrites: {report['import_changes']}")
    if 'validation' in report:
        v = report['validation']
        print(f"Validation: {'PASS' if v['valid'] else 'FAIL'} "
              f"({v['broken_count']} broken)")
    print(f"\n{report.get('message', '')}")
    if not report['success']:
        sys.exit(1)


if __name__ == '__main__':
    main()
