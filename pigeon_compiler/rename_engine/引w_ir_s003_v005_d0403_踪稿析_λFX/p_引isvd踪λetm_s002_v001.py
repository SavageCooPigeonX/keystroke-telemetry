"""引w_ir_s003_v005_d0403_踪稿析_λFX_extract_top_module_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 19 lines | ~163 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _extract_top_module(stripped: str) -> str:
    """Extract the top-level module from an import line.

    'from flask_wtf import ...' → 'flask_wtf'
    'import wtforms' → 'wtforms'
    'from auth.forms import ...' → 'auth'
    """
    if stripped.startswith('from '):
        parts = stripped[5:].split()
        if parts:
            return parts[0].split('.')[0]
    elif stripped.startswith('import '):
        parts = stripped[7:].split(',')[0].split()
        if parts:
            return parts[0].split('.')[0]
    return ''
