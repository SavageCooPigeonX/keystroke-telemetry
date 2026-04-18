"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_nametag_drift_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename
from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports
from pigeon_compiler.rename_engine.牌f_nam_s011_v004_d0401_追谱建踪_λA import scan_drift, scan_glyph_drift

def _run_heal_pipeline_nametag_drift(root: Path, execute: bool,
                                     manifests_only: bool,
                                     skip_rename: bool) -> dict:
    """Stage 1b: Nametag drift detection."""
    report_stage = {}
    if not manifests_only and not skip_rename:
        print('[1b/5] Checking nametag drift (desc vs docstring)...')
        drifts = scan_drift(root)
        report_stage = {
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
                report_stage['renamed'] = len(drift_result['renamed'])
                report_stage['import_changes'] = len(drift_changes)
                print(f'      {len(drift_result["renamed"])} nametag renames applied')
        elif drifts:
            print(f'      DRY RUN — {len(drifts)} files would be renamed for drift')
        else:
            print('      All nametags up to date')
    return report_stage
