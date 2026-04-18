"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_glyph_drift_decomposed_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename
from pigeon_compiler.rename_engine.审p_va_s005_v005_d0403_踪稿析_λFX import validate_imports
from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports
from pigeon_compiler.rename_engine.牌f_nam_s011_v004_d0401_追谱建踪_λA import scan_drift, scan_glyph_drift

def _run_heal_pipeline_glyph_drift(root: Path, execute: bool,
                                   manifests_only: bool,
                                   skip_rename: bool) -> dict:
    """Stage 1c: Glyph prefix drift detection."""
    report_stage = {}
    if not manifests_only and not skip_rename:
        print('[1c/5] Checking glyph prefix drift...')
        try:
            glyph_map, confidence_map, partner_data = _load_glyph_context(root)
            if glyph_map:
                glyph_drifts = scan_glyph_drift(
                    root, glyph_map, confidence_map, partners=partner_data,
                )
                report_stage = {
                    'drifted': len(glyph_drifts),
                    'files': [d['current'] + ' → ' + d['suggested']
                              for d in glyph_drifts[:20]],
                }
                if glyph_drifts and execute:
                    glyph_map_renames = {}
                    glyph_renames = []
                    for d in glyph_drifts:
                        old_path = d['path']
                        new_path = str(Path(old_path).parent / d['suggested'])
                        old_mod = old_path.replace('/', '.').replace('\\', '.').removesuffix('.py')
                        new_mod = new_path.replace('/', '.').replace('\\', '.').removesuffix('.py')
                        glyph_map_renames[old_mod] = new_mod
                        glyph_renames.append({
                            'old_path': old_path,
                            'new_path': new_path,
                            'old_module': old_mod,
                            'new_module': new_mod,
                        })
                    if glyph_renames:
                        print(f'      Rewriting imports for {len(glyph_renames)} glyph-drifted files...')
                        glyph_changes = rewrite_all_imports(root, glyph_map_renames, dry_run=False)
                        print(f'      Renaming {len(glyph_renames)} files for glyph update...')
                        glyph_plan = {'renames': glyph_renames, 'import_map': glyph_map_renames}
                        glyph_result = execute_rename(root, glyph_plan, dry_run=False)
                        report_stage['renamed'] = len(glyph_result['renamed'])
                        report_stage['import_changes'] = len(glyph_changes)
                        print(f'      {len(glyph_result["renamed"])} glyph renames applied')

                        print('      Validating imports after glyph renames...')
                        val = validate_imports(root)
                        report_stage['valid'] = val['valid']
                        if not val['valid']:
                            print(f'      WARNING: {len(val["broken"])} broken imports after glyph rename')
                            rollback_log = glyph_result.get('rollback_log')
                            if rollback_log:
                                from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import rollback_rename
                                print('      ROLLING BACK glyph renames...')
                                rb = rollback_rename(root, Path(rollback_log))
                                report_stage['rollback'] = {
                                    'restored': len(rb['restored']),
                                    'errors': rb['errors'],
                                }
                                inverted = {v: k for k, v in glyph_map_renames.items()}
                                rewrite_all_imports(root, inverted, dry_run=False)
                                print(f'      Rolled back {len(rb["restored"])} files')
                        else:
                            print('      Import validation passed')
                elif glyph_drifts:
                    print(f'      DRY RUN — {len(glyph_drifts)} files would get glyph update')
                else:
                    print('      All glyph prefixes current')
            else:
                report_stage = {'skipped': True, 'reason': 'no glyph map'}
                print('      No glyph map available — skipping')
        except Exception as e:
            report_stage = {'error': str(e)}
            print(f'      Glyph drift check failed: {e}')
    return report_stage
