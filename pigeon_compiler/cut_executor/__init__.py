"""cut_executor — Layer 3: Execute DeepSeek cut plans into real files.

Takes JSON cut plans, slices source by AST, writes Pigeon-compliant files,
fixes imports, writes manifests. The refactoring engine.
"""
from pigeon_compiler.cut_executor.析p_pp_s001_v004_d0315_测编深划鸽环_λν import parse_plan
from pigeon_compiler.cut_executor.切p_ss_s002_v004_d0315_重箱重助重拆_λν import slice_source
from pigeon_compiler.cut_executor.写w_fw_s003_v005_d0322_译改名踪_λμ import write_cut_files
from pigeon_compiler.cut_executor.踪p_if_s004_v004_d0315_牌册谱桥_λν import fix_imports
from pigeon_compiler.cut_executor.稿p_mw_s005_v004_d0315_册追跑谱桥_λν import write_manifest
from pigeon_compiler.cut_executor.验w_pv_s006_v004_d0315_重箱重拆追跑_λν import validate_plan
