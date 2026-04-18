"""批编f_rbc_s015_v002_d0328_织谱建验_λR_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 21 lines | ~143 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import sys, argparse, traceback, re

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SKIP_NAMES = frozenset({
    "setup.py", "conftest.py", "manage.py", "wsgi.py", "asgi.py",
    "test_all.py", "stress_test.py",  # test harness — not modules
})


SKIP_DIRS = frozenset({
    "__pycache__", ".git", ".venv", "node_modules",
    ".pytest_cache", "pigeon_code.egg-info", "dist",
})


COMPILER_DIRS = frozenset({
    "pigeon_compiler",
})
