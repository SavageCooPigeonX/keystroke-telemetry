"""Compatibility facade for split compile-lineage persistence."""

from .compile_lineage_compiled import (
    ALIAS_SCHEMA,
    SCHEMA,
    resolve_identity_alias,
    write_compile_lineage,
)

__all__ = ["ALIAS_SCHEMA", "SCHEMA", "resolve_identity_alias", "write_compile_lineage"]
