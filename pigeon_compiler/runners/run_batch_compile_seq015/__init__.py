"""run_batch_compile_seq015/ — Pigeon-compliant module."""
from pathlib import Path

from pigeon_compiler import _load_package_attrs

_PACKAGE_DIR = Path(__file__).resolve().parent

PROJECT_ROOT, main = _load_package_attrs(
	__name__,
	_PACKAGE_DIR,
	'seq001',
	'PROJECT_ROOT',
	'main',
)
COMPILER_DIRS, SKIP_DIRS, SKIP_NAMES, scan_oversized = _load_package_attrs(
	__name__,
	_PACKAGE_DIR,
	'seq002',
	'COMPILER_DIRS',
	'SKIP_DIRS',
	'SKIP_NAMES',
	'scan_oversized',
)
batch_compile = _load_package_attrs(
	__name__,
	_PACKAGE_DIR,
	'seq003',
	'batch_compile',
)

__all__ = [
	'PROJECT_ROOT',
	'main',
	'COMPILER_DIRS',
	'SKIP_DIRS',
	'SKIP_NAMES',
	'scan_oversized',
	'batch_compile',
]
