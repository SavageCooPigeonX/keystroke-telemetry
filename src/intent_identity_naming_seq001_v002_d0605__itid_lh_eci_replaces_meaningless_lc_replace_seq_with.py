"""Stable facade for the split intent-identity naming implementation."""

from .intent_identity_naming_seq001_v002_compiled import (
    INTENT_STEM_RE,
    LC_SEP,
    build_intent_filename,
    enrich_registry_entry,
    identity_id_from_path,
    intent_domain_for_path,
    itid_from_intent_key,
    lineage_hash,
    next_eci,
    parent_lineage_from_compile,
    parse_intent_stem,
    stamp_intent_touch,
)

__all__ = [
    "INTENT_STEM_RE",
    "LC_SEP",
    "build_intent_filename",
    "enrich_registry_entry",
    "identity_id_from_path",
    "intent_domain_for_path",
    "itid_from_intent_key",
    "lineage_hash",
    "next_eci",
    "parent_lineage_from_compile",
    "parse_intent_stem",
    "stamp_intent_touch",
]
