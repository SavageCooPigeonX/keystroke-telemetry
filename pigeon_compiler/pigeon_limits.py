"""Stable compatibility facade for the renamed Pigeon limits module."""

from .pigeon_limits_seq003_v001_d0730__central_compliance_thresholds_and_exclude_lc_organism_health_refactor import (
    EXCLUDE_DIR_PATTERNS,
    EXCLUDE_NAMES,
    EXCLUDE_STEM_PATTERNS,
    FILE_OVERHEAD,
    PIGEON_MAX,
    PIGEON_RECOMMENDED,
    explain_exclusion,
    is_excluded,
)

__all__ = [
    "EXCLUDE_DIR_PATTERNS",
    "EXCLUDE_NAMES",
    "EXCLUDE_STEM_PATTERNS",
    "FILE_OVERHEAD",
    "PIGEON_MAX",
    "PIGEON_RECOMMENDED",
    "explain_exclusion",
    "is_excluded",
]
