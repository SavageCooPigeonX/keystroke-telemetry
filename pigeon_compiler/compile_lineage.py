"""Stable compatibility facade for the renamed compile-lineage module."""

from .compile_lineage_seq002_v001_d0730__compatibility_facade_for_split_compile_lc_organism_health_refactor import (
    ALIAS_SCHEMA,
    SCHEMA,
    resolve_identity_alias,
    write_compile_lineage,
)

__all__ = [
    "ALIAS_SCHEMA",
    "SCHEMA",
    "resolve_identity_alias",
    "write_compile_lineage",
]
