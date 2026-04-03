"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_stage_save_registry_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc import (
    load_registry, save_registry, build_registry_from_scan,
    bump_all_versions,
)
from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project

def _run_heal_pipeline_save_registry(root: Path, report: dict):
    """Final: Save registry."""
    final_catalog = scan_project(root)
    registry = build_registry_from_scan(root, final_catalog)
    save_registry(root, registry)
    report['stages']['registry_save'] = {'entries': len(registry)}
    print(f'      Registry saved: {len(registry)} entries')
