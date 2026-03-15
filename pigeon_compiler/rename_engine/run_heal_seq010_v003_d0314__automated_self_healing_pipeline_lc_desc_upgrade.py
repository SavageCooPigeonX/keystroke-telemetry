"""run_heal_seq010_v001.py — Automated self-healing pipeline.

Runs on every push (via GitHub Actions) or locally.
Full pipeline: rename → rewrite imports → rebuild manifests → compliance → commit.

Usage:
  python -m pigeon_compiler.rename_engine.run_heal_seq010_v001 .
  python -m pigeon_compiler.rename_engine.run_heal_seq010_v001 . --execute
  python -m pigeon_compiler.rename_engine.run_heal_seq010_v001 . --manifests-only
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pigeon_compiler.rename_engine.scanner_seq001_v003_d0314__walk_the_project_tree_and_lc_desc_upgrade import scan_project
from pigeon_compiler.rename_engine.planner_seq002_v003_d0314__generate_rename_plan_for_non_lc_desc_upgrade import build_rename_plan
from pigeon_compiler.rename_engine.import_rewriter_seq003_v003_d0314__rewrite_all_imports_across_the_lc_desc_upgrade import rewrite_all_imports
from pigeon_compiler.rename_engine.executor_seq004_v003_d0314__execute_file_renames_with_rollback_lc_desc_upgrade import execute_rename
from pigeon_compiler.rename_engine.validator_seq005_v003_d0314__post_rename_import_validation_lc_desc_upgrade import validate_imports
from pigeon_compiler.rename_engine.manifest_builder_seq007_v003_d0314__generate_living_manifest_md_per_lc_desc_upgrade import build_all_manifests
from pigeon_compiler.rename_engine.compliance_seq008_v003_d0314__line_count_enforcer_split_recommender_lc_desc_upgrade import audit_compliance
from pigeon_compiler.rename_engine.nametag_seq011_v003_d0314__encode_file_description_intent_into_lc_desc_upgrade import scan_drift
from pigeon_compiler.rename_engine.registry_seq012_v003_d0314__local_name_registry_for_the_lc_desc_upgrade import (
    load_registry, save_registry, build_registry_from_scan,
    bump_all_versions,
)


def run_heal_pipeline(root: str, execute: bool = False,
                      manifests_only: bool = False,
                      skip_rename: bool = False,
                      intent: str = 'heal_pipeline') -> dict:
    """Full self-healing pipeline with registry tracking.

    1. Load/bootstrap registry
    2. Scan for non-Pigeon files → rename them
    3. Rewrite all imports
    4. Validate imports
    5. Rebuild all MANIFEST.md files
    6. Run compliance audit
    7. Save registry
    """
    root = Path(root).resolve()
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'root': str(root),
        'execute': execute,
        'stages': {},
    }

    # ── Stage 0: Load or bootstrap registry ──
    registry = load_registry(root)
    if not registry:
        print('[0/5] No registry found — bootstrapping from scan...')
        catalog = scan_project(root)
        registry = build_registry_from_scan(root, catalog)
        if execute:
            save_registry(root, registry)
        report['stages']['registry'] = {
            'action': 'bootstrapped', 'entries': len(registry),
        }
        print(f'      Registry bootstrapped: {len(registry)} entries')
    else:
        report['stages']['registry'] = {
            'action': 'loaded', 'entries': len(registry),
        }
        print(f'[0/5] Registry loaded: {len(registry)} entries')

    # ── Stage 1: Rename non-compliant files ──
    if not manifests_only and not skip_rename:
        print('[1/5] Scanning for non-Pigeon files...')
        catalog = scan_project(root)
        non_compliant = catalog['stats']['non_compliant']
        report['stages']['scan'] = catalog['stats']

        if non_compliant > 0:
            print(f'      Found {non_compliant} non-compliant files')
            plan = build_rename_plan(catalog, root=root, intent=intent)
            renames = plan.get('renames', [])
            report['stages']['plan'] = {
                'renames_planned': len(renames),
                'files': [r['old_path'] + ' → ' + r['new_path']
                          for r in renames[:20]],
            }

            if execute and renames:
                # Rewrite imports first
                print(f'[2/5] Rewriting imports ({len(plan.get("import_map", {}))} mappings)...')
                changes = rewrite_all_imports(root, plan['import_map'],
                                              dry_run=False)
                report['stages']['import_rewrite'] = len(changes)
                print(f'      Rewrote {len(changes)} import lines')

                # Execute renames
                print(f'[3/5] Renaming {len(renames)} files...')
                result = execute_rename(root, plan, dry_run=False)
                report['stages']['rename'] = {
                    'renamed': len(result['renamed']),
                    'errors': result['errors'],
                }
                print(f'      Renamed {len(result["renamed"])} files')

                # Validate
                print('[4/5] Validating imports...')
                val = validate_imports(root)
                report['stages']['validate'] = {
                    'valid': val['valid'],
                    'broken': len(val['broken']),
                }
                if not val['valid']:
                    print(f'      WARNING: {len(val["broken"])} broken imports')
            else:
                print('      DRY RUN — no renames executed')
                report['stages']['rename'] = {'dry_run': True}
        else:
            print('      All files already Pigeon-compliant')
            report['stages']['rename'] = {'skipped': True, 'reason': 'all compliant'}
    else:
        print('[1/5] Rename skipped')

    # ── Stage 1b: Nametag drift detection ──
    if not manifests_only and not skip_rename:
        print('[1b/5] Checking nametag drift (desc vs docstring)...')
        drifts = scan_drift(root)
        report['stages']['nametag_drift'] = {
            'drifted': len(drifts),
            'files': [d['current'] + ' → ' + d['suggested']
                      for d in drifts[:20]],
        }
        if drifts and execute:
            drift_map = {}
            drift_renames = []
            for d in drifts:
                old_path = d['path']
                new_path = str(Path(old_path).parent / d['suggested'])
                old_mod = old_path.replace('/', '.').replace('\\', '.').removesuffix('.py')
                new_mod = new_path.replace('/', '.').replace('\\', '.').removesuffix('.py')
                drift_map[old_mod] = new_mod
                drift_renames.append({
                    'old_path': old_path,
                    'new_path': new_path,
                    'old_module': old_mod,
                    'new_module': new_mod,
                })

            if drift_renames:
                print(f'      Rewriting imports for {len(drift_renames)} drifted files...')
                drift_changes = rewrite_all_imports(root, drift_map, dry_run=False)
                print(f'      Renaming {len(drift_renames)} drifted files...')
                drift_plan = {'renames': drift_renames, 'import_map': drift_map}
                drift_result = execute_rename(root, drift_plan, dry_run=False)
                report['stages']['nametag_drift']['renamed'] = len(drift_result['renamed'])
                report['stages']['nametag_drift']['import_changes'] = len(drift_changes)
                print(f'      {len(drift_result["renamed"])} nametag renames applied')
        elif drifts:
            print(f'      DRY RUN — {len(drifts)} files would be renamed for drift')
        else:
            print('      All nametags up to date')

    # ── Stage 2: Rebuild all MANIFESTs ──
    stage_num = '5' if not manifests_only else '1'
    print(f'[{stage_num}/5] Rebuilding MANIFEST.md files...')
    manifest_results = build_all_manifests(root, dry_run=not execute)
    wrote = sum(1 for r in manifest_results if r.get('wrote'))
    report['stages']['manifests'] = {
        'total_folders': len(manifest_results),
        'written': wrote,
    }
    print(f'      {len(manifest_results)} folders scanned, {wrote} manifests written')

    # ── Stage 3: Compliance audit ──
    print(f'[5/5] Running compliance audit...')
    compliance = audit_compliance(root)
    report['stages']['compliance'] = {
        'total': compliance['total'],
        'compliant': compliance['compliant'],
        'pct': compliance['compliance_pct'],
        'oversize': len(compliance['oversize']),
        'critical': [e['path'] for e in compliance['oversize']
                     if e['status'] == 'CRITICAL'],
    }
    print(f'      Compliance: {compliance["compliant"]}/{compliance["total"]} '
          f'({compliance["compliance_pct"]}%)')

    # ── Final: Save registry ──
    if execute:
        # Re-scan to capture any renames that happened
        final_catalog = scan_project(root)
        registry = build_registry_from_scan(root, final_catalog)
        save_registry(root, registry)
        report['stages']['registry_save'] = {'entries': len(registry)}
        print(f'      Registry saved: {len(registry)} entries')

    report['success'] = True
    return report


def git_commit_changes(root: Path, message: str) -> bool:
    """Stage and commit all changes made by the heal pipeline."""
    try:
        # Stage MANIFEST.md files and any renamed .py files
        subprocess.run(['git', 'add', '-A'], cwd=str(root),
                       capture_output=True, timeout=30)

        # Check if there are changes to commit
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            cwd=str(root), capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            print('No changes to commit.')
            return False

        subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=str(root), capture_output=True, timeout=30,
        )
        print(f'Committed: {message}')
        return True
    except Exception as e:
        print(f'Git commit failed: {e}')
        return False


def format_report(report: dict) -> str:
    """Human-readable report."""
    lines = ['=== PIGEON HEAL REPORT ===', '']
    stages = report.get('stages', {})

    if 'scan' in stages:
        s = stages['scan']
        lines.append(f'Scan: {s.get("total", 0)} files, '
                     f'{s.get("non_compliant", 0)} non-compliant')

    if 'rename' in stages:
        r = stages['rename']
        if r.get('dry_run'):
            lines.append('Rename: DRY RUN (use --execute to apply)')
        elif r.get('skipped'):
            lines.append('Rename: skipped (all compliant)')
        else:
            lines.append(f'Rename: {r.get("renamed", 0)} files renamed')

    if 'import_rewrite' in stages:
        lines.append(f'Imports: {stages["import_rewrite"]} lines rewritten')

    if 'validate' in stages:
        v = stages['validate']
        status = 'PASS' if v.get('valid') else f'FAIL ({v.get("broken", 0)} broken)'
        lines.append(f'Validate: {status}')

    if 'nametag_drift' in stages:
        nd = stages['nametag_drift']
        renamed = nd.get('renamed', 0)
        if nd.get('drifted', 0):
            lines.append(f'Nametag: {nd["drifted"]} drifted, {renamed} renamed')
        else:
            lines.append('Nametag: all descriptions current')

    if 'manifests' in stages:
        m = stages['manifests']
        lines.append(f'Manifests: {m.get("written", 0)}/{m.get("total_folders", 0)} written')

    if 'compliance' in stages:
        c = stages['compliance']
        lines.append(f'Compliance: {c.get("compliant", 0)}/{c.get("total", 0)} '
                     f'({c.get("pct", 0)}%) — {c.get("oversize", 0)} oversize')
        crits = c.get('critical', [])
        if crits:
            lines.append(f'Critical ({len(crits)}):')
            for p in crits[:10]:
                lines.append(f'  🔴 {p}')

    return '\n'.join(lines)


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


if __name__ == '__main__':
    main()
