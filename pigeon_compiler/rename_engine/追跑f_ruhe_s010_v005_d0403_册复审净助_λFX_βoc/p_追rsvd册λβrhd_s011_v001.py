"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_run_heal_decomposed_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename
from pigeon_compiler.rename_engine.w_pl_s002_v005_d0401_册追跑谱桥_λA import build_rename_plan
from pigeon_compiler.rename_engine.册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc import (
    load_registry, save_registry, build_registry_from_scan,
    bump_all_versions,
)
from pigeon_compiler.rename_engine.审p_va_s005_v005_d0403_踪稿析_λFX import validate_imports
from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports
from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project
from pigeon_compiler.rename_engine.正f_cmp_s008_v004_d0315_踪稿析_λν import audit_compliance
from pigeon_compiler.rename_engine.牌f_nam_s011_v004_d0401_追谱建踪_λA import scan_drift, scan_glyph_drift
from pigeon_compiler.rename_engine.谱建f_mb_s007_v003_d0314_观重箱重拆_λD import build_all_manifests

def run_heal_pipeline(root: str, execute: bool = False,
                      manifests_only: bool = False,
                      skip_rename: bool = False,
                      intent: str = 'heal_pipeline') -> dict:
    """Full self-healing pipeline with registry tracking."""
    from pathlib import Path
    from datetime import datetime, timezone
    from pigeon_compiler.registry import (load_registry, save_registry,
                                          build_registry_from_scan)
    from pigeon_compiler.scanner import scan_project
    from pigeon_compiler.rename_engine import (build_rename_plan,
                                               execute_rename,
                                               rewrite_all_imports,
                                               validate_imports,
                                               scan_drift,
                                               scan_glyph_drift)
    from pigeon_compiler.manifest import build_all_manifests
    from pigeon_compiler.audit import audit_compliance
    from pigeon_compiler.glyph_context import _load_glyph_context

    root = Path(root).resolve()
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'root': str(root),
        'execute': execute,
        'stages': {},
    }

    # Stage 0: Load or bootstrap registry
    registry, report['stages']['registry'] = _run_heal_pipeline_load_registry(root, execute)

    # Stage 1: Rename non-compliant files
    rename_report = _run_heal_pipeline_rename_non_compliant(root, execute, manifests_only, skip_rename, intent)
    report['stages'].update(rename_report)

    # Stage 1b: Nametag drift detection
    if not manifests_only and not skip_rename:
        report['stages']['nametag_drift'] = _run_heal_pipeline_nametag_drift(root, execute, manifests_only, skip_rename)

    # Stage 1c: Glyph prefix drift detection
    if not manifests_only and not skip_rename:
        report['stages']['glyph_drift'] = _run_heal_pipeline_glyph_drift(root, execute, manifests_only, skip_rename)

    # Stage 2: Rebuild all MANIFESTs
    report['stages']['manifests'] = _run_heal_pipeline_rebuild_manifests(root, execute, manifests_only)

    # Stage 3: Compliance audit
    report['stages']['compliance'] = _run_heal_pipeline_compliance_audit(root)

    # Final: Save registry
    if execute:
        report['stages']['registry_save'] = _run_heal_pipeline_save_registry(root, execute)

    report['success'] = True
    return report
