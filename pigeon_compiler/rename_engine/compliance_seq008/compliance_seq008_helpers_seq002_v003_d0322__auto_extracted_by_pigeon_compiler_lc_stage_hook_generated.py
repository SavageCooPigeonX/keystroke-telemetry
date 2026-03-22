"""compliance_seq008_helpers_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v003 | 26 lines | ~227 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_hook_generated
# LAST:   2026-03-22 @ b48ee0a
# SESSIONS: 2
# ──────────────────────────────────────────────
from pathlib import Path
import re
from .compliance_seq008_constants_seq001_v001 import SKIP_DIRS

def _snake(name: str) -> str:
    """Convert CamelCase or title to snake_case."""
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'([A-Z])', r'_\1', name).lower()
    return re.sub(r'_+', '_', name).strip('_')


def _should_skip(py: Path, root: Path) -> bool:
    parts = py.relative_to(root).parts
    for p in parts:
        if p in SKIP_DIRS or p.startswith('.venv') or p.startswith('_llm_tests'):
            return True
    return False
