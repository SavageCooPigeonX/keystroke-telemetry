"""Command-line facade for the split organization planner."""

from .organization_pass_seq001_v001_compiled import (
    FileInfo,
    HISTORY,
    LATEST,
    MARKDOWN,
    MAX_PY_LINES,
    ROOT_SRC_FAMILIES,
    SCHEMA,
    SKIP_PARTS,
    TOP_SOURCE_DIRS,
    build_organization_plan,
    main,
    render_organization_plan,
)

__all__ = [
    "FileInfo",
    "HISTORY",
    "LATEST",
    "MARKDOWN",
    "MAX_PY_LINES",
    "ROOT_SRC_FAMILIES",
    "SCHEMA",
    "SKIP_PARTS",
    "TOP_SOURCE_DIRS",
    "build_organization_plan",
    "main",
    "render_organization_plan",
]

if __name__ == "__main__":
    raise SystemExit(main())
