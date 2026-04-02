"""rename_engine — Atomic whole-codebase rename with import rewriting.

Renames files and folders to Pigeon Code convention (_seqNNN_vNNN.py)
and fixes every import across the entire project in one pass.
Includes self-healing manifests that track operator intent.
"""
from pathlib import Path

from pigeon_compiler import _load_package_attrs

_PACKAGE_DIR = Path(__file__).resolve().parent

scan_project = _load_package_attrs(__name__, _PACKAGE_DIR, 's001', 'scan_project')
build_rename_plan = _load_package_attrs(__name__, _PACKAGE_DIR, 's002', 'build_rename_plan')
rewrite_all_imports = _load_package_attrs(__name__, _PACKAGE_DIR, 's003', 'rewrite_all_imports')
execute_rename = _load_package_attrs(__name__, _PACKAGE_DIR, 's004', 'execute_rename')
validate_imports = _load_package_attrs(__name__, _PACKAGE_DIR, 's005', 'validate_imports')
run_full_rename = _load_package_attrs(__name__, _PACKAGE_DIR, 's006', 'run_full_rename')
build_all_manifests, sync_master_structure = _load_package_attrs(
    __name__,
    _PACKAGE_DIR,
    's007',
    'build_all_manifests',
    'sync_master_structure',
)
audit_compliance = _load_package_attrs(__name__, _PACKAGE_DIR, 's008', 'audit_compliance')
heal = _load_package_attrs(__name__, _PACKAGE_DIR, 's009', 'heal')
run_heal_pipeline = _load_package_attrs(__name__, _PACKAGE_DIR, 's010', 'run_heal_pipeline')
extract_desc_slug, build_nametag, scan_drift = _load_package_attrs(
    __name__,
    _PACKAGE_DIR,
    's011',
    'extract_desc_slug',
    'build_nametag',
    'scan_drift',
)
load_registry, save_registry, build_registry_from_scan, build_pigeon_filename, parse_pigeon_stem, bump_version, bump_all_versions, build_compressed_filename, mutate_compressed_stem, bug_keys_from_marker, bug_marker_from_keys = _load_package_attrs(
    __name__,
    _PACKAGE_DIR,
    's012',
    'load_registry',
    'save_registry',
    'build_registry_from_scan',
    'build_pigeon_filename',
    'parse_pigeon_stem',
    'bump_version',
    'bump_all_versions',
    'build_compressed_filename',
    'mutate_compressed_stem',
    'bug_keys_from_marker',
    'bug_marker_from_keys',
)

__all__ = [
    'scan_project',
    'build_rename_plan',
    'rewrite_all_imports',
    'execute_rename',
    'validate_imports',
    'run_full_rename',
    'build_all_manifests',
    'sync_master_structure',
    'audit_compliance',
    'heal',
    'run_heal_pipeline',
    'extract_desc_slug',
    'build_nametag',
    'scan_drift',
    'load_registry',
    'save_registry',
    'build_registry_from_scan',
    'build_pigeon_filename',
    'parse_pigeon_stem',
    'bump_version',
    'bump_all_versions',
    'build_compressed_filename',
    'mutate_compressed_stem',
    'bug_keys_from_marker',
    'bug_marker_from_keys',
]
