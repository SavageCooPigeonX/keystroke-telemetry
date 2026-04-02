"""cut_executor — Layer 3: Execute DeepSeek cut plans into real files.

Takes JSON cut plans, slices source by AST, writes Pigeon-compliant files,
fixes imports, writes manifests. The refactoring engine.
"""
from pathlib import Path

from pigeon_compiler import _load_package_attrs

_PACKAGE_DIR = Path(__file__).resolve().parent

parse_plan = _load_package_attrs(__name__, _PACKAGE_DIR, 's001', 'parse_plan')
slice_source = _load_package_attrs(__name__, _PACKAGE_DIR, 's002', 'slice_source')
write_cut_files = _load_package_attrs(__name__, _PACKAGE_DIR, 's003', 'write_cut_files')
fix_imports = _load_package_attrs(__name__, _PACKAGE_DIR, 's004', 'fix_imports')
write_manifest = _load_package_attrs(__name__, _PACKAGE_DIR, 's005', 'write_manifest')
validate_plan = _load_package_attrs(__name__, _PACKAGE_DIR, 's006', 'validate_plan')

__all__ = [
	'parse_plan',
	'slice_source',
	'write_cut_files',
	'fix_imports',
	'write_manifest',
	'validate_plan',
]
