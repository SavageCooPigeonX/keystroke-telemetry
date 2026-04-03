"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_stage_load_registry_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc import (
    load_registry, save_registry, build_registry_from_scan,
    bump_all_versions,
)
from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project

def _run_heal_pipeline_load_registry(root: Path, report: dict, execute: bool):
    """Stage 0: Load or bootstrap registry."""
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
    return registry
