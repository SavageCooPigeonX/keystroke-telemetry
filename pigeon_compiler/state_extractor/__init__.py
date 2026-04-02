"""state_extractor/ — Layer 1: Pure AST analysis, zero API calls.

Maps functions, call graphs, imports, shared state, and resistance
patterns for any Python file. Produces Ether Map JSON.
"""
from pathlib import Path

from pigeon_compiler import _load_package_attrs

build_ether_map = _load_package_attrs(
	__name__,
	Path(__file__).resolve().parent,
	's006',
	'build_ether_map',
)

__all__ = ['build_ether_map']
