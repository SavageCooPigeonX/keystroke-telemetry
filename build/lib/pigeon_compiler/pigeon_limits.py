"""pigeon_limits.py — Central compliance thresholds and exclude logic.

Two-tier system:
  PIGEON_RECOMMENDED (50)  — target line count, generates warnings
  PIGEON_MAX         (200) — hard cap, blocks compliance

Exclude logic:
  is_excluded(path) returns True for files that skip compliance checks.
  Excluded: __init__.py, prompts, app.py, conftest.py, _llm_tests scripts,
            Railway entry points, static/, templates/, .github/.
"""
import re
from pathlib import Path

PIGEON_RECOMMENDED = 50
PIGEON_MAX = 200
FILE_OVERHEAD = 5

# --- Files that CANNOT be renamed ---
# These are referenced by external systems (Procfile, railway.json,
# GitHub Actions, Flask send_from_directory / render_template).
# Renaming them kills production or breaks CI.  The pigeon rename
# engine was the actual root cause of a multi-day worker outage
# (commit 4182ecd).

EXCLUDE_NAMES = frozenset({
    "__init__.py",
    "conftest.py",
    "app.py",
    "Procfile",
    "requirements.txt",
    "nixpacks.toml",
    "railway.json",
    "railway.worker.json",
    "pigeon_registry.json",
})

# Directories whose contents must never be renamed.
# static/  — HTML/CSS/JS served by send_from_directory(), paths hardcoded
# templates/ — Jinja2 templates loaded by render_template(), paths hardcoded
# .github/  — CI workflow YAML references module paths by exact string
EXCLUDE_DIR_PATTERNS = frozenset({
    "_llm_tests_put_all_test_and_debug_scripts_here",
    "__pycache__",
    ".venv",
    "node_modules",
    "static",
    "templates",
    ".github",
    "audit_backups",
    "json_uploads",
    "documentation",
    "maif_propaganda",
    "logs",
})

# Any file whose stem or path contains these substrings is excluded
EXCLUDE_STEM_PATTERNS = re.compile(
    r"prompt|_prompt_|deepseek_plan_prompt", re.IGNORECASE
)


def is_excluded(path: Path, root: Path = None) -> bool:
    """Return True if path should be excluded from compliance checks."""
    if path.name in EXCLUDE_NAMES:
        return True
    parts = path.parts
    for d in EXCLUDE_DIR_PATTERNS:
        if d in parts:
            return True
    if EXCLUDE_STEM_PATTERNS.search(path.stem):
        return True
    # Non-Python files are never candidates for pigeon rename
    if path.suffix and path.suffix != ".py":
        return True
    return False
