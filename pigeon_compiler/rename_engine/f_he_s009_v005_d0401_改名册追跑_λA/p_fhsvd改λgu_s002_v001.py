"""f_he_s009_v005_d0401_改名册追跑_λA_git_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 39 lines | ~359 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
import subprocess

def _git_changed_files(root: Path) -> list[str]:
    """Get files changed since last heal (or last commit)."""
    # Try: changed in working tree + staged
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = [f for f in result.stdout.strip().split('\n')
                     if f.endswith('.py')]
            return files
    except Exception:
        pass

    # Fallback: all tracked .py files
    return _all_py_files(root)


def _all_py_files(root: Path) -> list[str]:
    """List all non-skipped .py files."""
    skip = {'.venv', '__pycache__', 'node_modules', '.git',
            '_llm_tests_put_all_test_and_debug_scripts_here',
            '.pytest_cache', 'rollback_logs', 'audit_backups',
            'json_uploads', 'logs', 'cache'}
    files = []
    for py in sorted(root.rglob('*.py')):
        parts = py.relative_to(root).parts
        if any(p in skip or p.startswith('.venv') or
               p.startswith('_llm_tests') for p in parts):
            continue
        files.append(str(py.relative_to(root)).replace('\\', '/'))
    return files
