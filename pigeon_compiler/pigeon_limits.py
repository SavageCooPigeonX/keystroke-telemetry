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
# vscode-extension/ — entry points invoked directly by the VS Code extension
# client/ — standalone scripts with __main__ blocks, not importable packages
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
    "vscode-extension",
    "client",
})

# Any file whose stem STARTS WITH or CONTAINS these patterns is excluded.
# Categories:
#   prompt_* / deepseek_plan_prompt — prompt templates, never split (LLM instructions)
#   run_clean_split / run_pigeon_loop / run_heal — compiler orchestrators:
#     splitting them mid-run causes import-of-partially-written-package crashes
#   streaming_layer_seq007 — intentional 1150-line test harness (see copilot-instructions)
#   stress_test / test_all / deep_test / test_public — root-level test runners
EXCLUDE_STEM_PATTERNS = re.compile(
    r"^(?:prompt_"
    r"|deepseek_plan_prompt"
    r"|run_clean_split"
    r"|run_pigeon_loop"
    r"|run_heal_seq"
    r"|streaming_layer_seq007"
    r"|stress_test"
    r"|test_all"
    r"|deep_test"
    r"|test_public"
    r")",
    re.IGNORECASE,
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
