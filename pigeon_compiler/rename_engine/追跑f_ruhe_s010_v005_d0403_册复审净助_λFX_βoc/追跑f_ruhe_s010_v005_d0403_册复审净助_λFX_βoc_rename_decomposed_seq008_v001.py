"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_rename_decomposed_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename
from pigeon_compiler.rename_engine.w_pl_s002_v005_d0401_册追跑谱桥_λA import build_rename_plan
from pigeon_compiler.rename_engine.审p_va_s005_v005_d0403_踪稿析_λFX import validate_imports
from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports
from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project

def _run_heal_pipeline_rename_non_compliant(root: Path, execute: bool,
                                            manifests_only: bool,
                                            skip_rename: bool,
                                            intent: str) -> dict:
    """Stage 1: Rename non-compliant files."""
    report_stage = {}
    if not manifests_only and not skip_rename:
        print('[1/5] Scanning for non-Pigeon files...')
        catalog = scan_project(root)
        non_compliant = catalog['stats']['non_compliant']
        report_stage['scan'] = catalog['stats']

        if non_compliant > 0:
            print(f'      Found {non_compliant} non-compliant files')
            plan = build_rename_plan(catalog, root=root, intent=intent)
            renames = plan.get('renames', [])
            report_stage['plan'] = {
                'renames_planned': len(renames),
                'files': [r['old_path'] + ' → ' + r['new_path']
                          for r in renames[:20]],
            }

            if execute and renames:
                print(f'[2/5] Rewriting imports ({len(plan.get("import_map", {}))} mappings)...')
                changes = rewrite_all_imports(root, plan['import_map'],
                                              dry_run=False)
                report_stage['import_rewrite'] = len(changes)
                print(f'      Rewrote {len(changes)} import lines')

                print(f'[3/5] Renaming {len(renames)} files...')
                result = execute_rename(root, plan, dry_run=False)
                report_stage['rename'] = {
                    'renamed': len(result['renamed']),
                    'errors': result['errors'],
                }
                print(f'      Renamed {len(result["renamed"])} files')

                print('[4/5] Validating imports...')
                val = validate_imports(root)
                report_stage['validate'] = {
                    'valid': val['valid'],
                    'broken': len(val['broken']),
                }
                if not val['valid']:
                    print(f'      WARNING: {len(val["broken"])} broken imports')
            else:
                print('      DRY RUN — no renames executed')
                report_stage['rename'] = {'dry_run': True}
        else:
            print('      All files already Pigeon-compliant')
            report_stage['rename'] = {'skipped': True, 'reason': 'all compliant'}
    else:
        print('[1/5] Rename skipped')
    return report_stage
