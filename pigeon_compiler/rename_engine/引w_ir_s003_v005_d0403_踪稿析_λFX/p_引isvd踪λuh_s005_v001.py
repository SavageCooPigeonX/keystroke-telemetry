"""引w_ir_s003_v005_d0403_踪稿析_λFX_utility_helpers_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 33 lines | ~241 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re
from .p_引isvd踪λc_s001_v001 import KNOWN_EXTERNAL, SKIP_DIRS

def _build_stem_map(import_map: dict) -> dict:
    """Map old stems to new modules for partial matches."""
    stem_map = {}
    for old_mod, new_mod in import_map.items():
        old_stem = old_mod.rsplit('.', 1)[-1]
        stem_map[old_stem] = (old_mod, new_mod)
    return stem_map


def _has_any_reference(text: str, import_map: dict, stem_map: dict) -> bool:
    for old_mod in import_map:
        if old_mod in text:
            return True
    for stem in stem_map:
        if stem in text:
            return True
    return False


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def _should_skip(py: Path, root: Path) -> bool:
    parts = py.relative_to(root).parts
    return any(p in SKIP_DIRS for p in parts)
