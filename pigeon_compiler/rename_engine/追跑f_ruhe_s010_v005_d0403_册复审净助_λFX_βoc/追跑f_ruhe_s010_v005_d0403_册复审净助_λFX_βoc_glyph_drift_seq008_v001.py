"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_glyph_drift_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.牌f_nam_s011_v004_d0401_追谱建踪_λA import scan_drift, scan_glyph_drift

def _run_heal_pipeline_glyph_drift(root: Path, report: dict, execute: bool):
    """Stage 1c: Glyph prefix drift detection."""
    print('[1c/5] Checking glyph prefix drift...')
    try:
        glyph_map, confidence_map, partner_data = _load_glyph_context(root)
        if glyph_map:
            glyph_drifts = scan_glyph_drift(
                root, glyph_map, confidence_map, partners=partner_data,
            )
            report['stages']['glyph_drift'] = {
                'drifted': len(glyph_drifts),
                'files': [d['current'] + ' → ' + d['suggested']
                          for d in glyph_drifts[:20]],
            }
            if glyph_drifts and execute:
                _run_heal_pipeline_execute_glyph_renames(root, report, glyph_drifts)
            elif glyph_drifts:
                print(f'      DRY RUN — {len(glyph_drifts)} files would get glyph update')
            else:
                print('      All glyph prefixes current')
        else:
            report['stages']['glyph_drift'] = {'skipped': True, 'reason': 'no glyph map'}
            print('      No glyph map available — skipping')
    except Exception as e:
        report['stages']['glyph_drift'] = {'error': str(e)}
        print(f'      Glyph drift check failed: {e}')
