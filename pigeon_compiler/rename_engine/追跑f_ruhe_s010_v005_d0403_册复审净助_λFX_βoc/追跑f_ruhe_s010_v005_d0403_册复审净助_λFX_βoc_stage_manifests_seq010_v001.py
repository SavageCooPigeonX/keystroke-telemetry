"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_stage_manifests_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.谱建f_mb_s007_v003_d0314_观重箱重拆_λD import build_all_manifests

def _run_heal_pipeline_manifests(root: Path, report: dict, execute: bool,
                                 manifests_only: bool):
    """Stage 2: Rebuild all MANIFESTs."""
    stage_num = '5' if not manifests_only else '1'
    print(f'[{stage_num}/5] Rebuilding MANIFEST.md files...')
    manifest_results = build_all_manifests(root, dry_run=not execute)
    wrote = sum(1 for r in manifest_results if r.get('wrote'))
    report['stages']['manifests'] = {
        'total_folders': len(manifest_results),
        'written': wrote,
    }
    print(f'      {len(manifest_results)} folders scanned, {wrote} manifests written')
