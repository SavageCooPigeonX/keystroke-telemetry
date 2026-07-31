"""Compatibility facade for split folder context coupling."""

from .folder_context_coupling_seq001_v001_compiled import (
    AST_IDENTITY_FILE_CAP,
    FILE_SCAN_CAP,
    HISTORY,
    LATEST,
    MARKDOWN,
    OVERCAP_LINE_LIMIT,
    PACKAGE_RANK_SCAN_CAP,
    build_folder_context_coupling,
    render_folder_context_coupling,
)

__all__ = [
    "AST_IDENTITY_FILE_CAP",
    "FILE_SCAN_CAP",
    "HISTORY",
    "LATEST",
    "MARKDOWN",
    "OVERCAP_LINE_LIMIT",
    "PACKAGE_RANK_SCAN_CAP",
    "build_folder_context_coupling",
    "render_folder_context_coupling",
]
