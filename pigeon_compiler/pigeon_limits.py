"""pigeon_limits.py — Central compliance thresholds and exclude logic.

Two-tier system:
  PIGEON_RECOMMENDED (50)  — target line count, generates warnings
  PIGEON_MAX         (200) — hard cap, blocks compliance

Exclude logic:
  is_excluded(path) returns True for files that skip compliance checks.
  Excluded: __init__.py, prompts, app.py, conftest.py, _llm_tests scripts.
"""
import re
from pathlib import Path

PIGEON_RECOMMENDED = 50
PIGEON_MAX = 200
FILE_OVERHEAD = 5

# Patterns for files excluded from compliance checks
EXCLUDE_NAMES = frozenset({
    "__init__.py",
    "conftest.py",
    "app.py",
})

EXCLUDE_DIR_PATTERNS = frozenset({
    "_llm_tests_put_all_test_and_debug_scripts_here",
    "__pycache__",
    ".venv",
    "node_modules",
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
    return False
