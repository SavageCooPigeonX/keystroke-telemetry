"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_orchestrator_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from pigeon_compiler.rename_engine.册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc import (
    load_registry, save_registry, build_registry_from_scan,
    bump_all_versions,
)

def run_heal_pipeline(root: str, execute: bool = False,
                      manifests_only: bool = False,
                      skip_rename: bool = False,
                      intent: str = 'heal_pipeline') -> dict:
    """Full self-healing pipeline with registry tracking."""
    root = Path(root).resolve()
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'root': str(root),
        'execute': execute,
        'stages': {},
    }

    registry = _run_heal_pipeline_load_registry(root, report, execute)
    if not manifests_only and not skip_rename:
        _run_heal_pipeline_rename_stage(root, report, execute, intent, registry)
        _run_heal_pipeline_nametag_drift(root, report, execute)
        _run_heal_pipeline_glyph_drift(root, report, execute)
    _run_heal_pipeline_manifests(root, report, execute, manifests_only)
    _run_heal_pipeline_compliance(root, report)
    if execute:
        _run_heal_pipeline_save_registry(root, report)
    report['success'] = True
    return report
