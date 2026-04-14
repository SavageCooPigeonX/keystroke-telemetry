"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_should_skip_seq019_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v001 | 10 lines | ~92 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _should_skip(py: Path, root: Path) -> bool:
    parts = py.relative_to(root).parts
    for p in parts:
        if p in SKIP_DIRS or p.startswith('.venv') or p.startswith('_llm_tests'):
            return True
    return False
