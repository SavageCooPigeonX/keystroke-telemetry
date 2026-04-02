"""rename_engine — Atomic whole-codebase rename with import rewriting.

Renames files and folders to Pigeon Code convention (_seqNNN_vNNN.py)
and fixes every import across the entire project in one pass.
Includes self-healing manifests that track operator intent.
"""
from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project
from pigeon_compiler.rename_engine.w_pl_s002_v005_d0401_册追跑谱桥_λA import build_rename_plan
from pigeon_compiler.rename_engine.引w_ir_s003_v004_d0316_踪稿析_λΞ import rewrite_all_imports
from pigeon_compiler.rename_engine.p_ex_s004_v004_d0315_册追跑复审_λν import execute_rename
from pigeon_compiler.rename_engine.审p_va_s005_v004_d0315_踪稿析_λν import validate_imports
from pigeon_compiler.rename_engine.改名f_rr_s006_v005_d0401_追跑拆谱建_λA import run_full_rename
from pigeon_compiler.rename_engine.谱建f_mb_s007_v003_d0314_观重箱重拆_λD import build_all_manifests, sync_master_structure
from pigeon_compiler.rename_engine.正f_cmp_s008_v004_d0315_踪稿析_λν import audit_compliance
from pigeon_compiler.rename_engine.f_he_s009_v005_d0401_改名册追跑_λA import heal
from pigeon_compiler.rename_engine.追跑f_ruhe_s010_v004_d0315_册复审净助_λν import run_heal_pipeline
from pigeon_compiler.rename_engine.牌f_nam_s011_v004_d0401_追谱建踪_λA import (
    extract_desc_slug, build_nametag, scan_drift,
)
from pigeon_compiler.rename_engine.册f_reg_s012_v004_d0401_追跑谱桥复审_λA import (
    load_registry, save_registry, build_registry_from_scan,
    build_pigeon_filename, parse_pigeon_stem,
    bump_version, bump_all_versions,
)
