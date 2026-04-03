"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_execute_glyph_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename
from pigeon_compiler.rename_engine.审p_va_s005_v005_d0403_踪稿析_λFX import validate_imports
from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports

def _run_heal_pipeline_execute_glyph_renames(root: Path, report: dict, glyph_drifts: list):
    """Execute glyph renames and validate."""
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
        report['stages']['glyph_drift']['renamed'] = len(glyph_result['renamed'])
        report['stages']['glyph_drift']['import_changes'] = len(glyph_changes)
        print(f'      {len(glyph_result["renamed"])} glyph renames applied')

        print('      Validating imports after glyph renames...')
        val = validate_imports(root)
        report['stages']['glyph_drift']['valid'] = val['valid']
        if not val['valid']:
            print(f'      WARNING: {len(val["broken"])} broken imports after glyph rename')
            rollback_log = glyph_result.get('rollback_log')
            if rollback_log:
                from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import rollback_rename
                print('      ROLLING BACK glyph renames...')
                rb = rollback_rename(root, Path(rollback_log))
                report['stages']['glyph_drift']['rollback'] = {
                    'restored': len(rb['restored']),
                    'errors': rb['errors'],
                }
                inverted = {v: k for k, v in glyph_map_renames.items()}
                rewrite_all_imports(root, inverted, dry_run=False)
                print(f'      Rolled back {len(rb["restored"])} files')
        else:
            print('      Import validation passed')
