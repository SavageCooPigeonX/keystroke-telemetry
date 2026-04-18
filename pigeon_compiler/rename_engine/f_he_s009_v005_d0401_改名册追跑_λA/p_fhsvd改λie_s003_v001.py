"""f_he_s009_v005_d0401_改名册追跑_λA_intent_extract_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 36 lines | ~254 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _extract_intent(py: Path) -> str:
    """Extract intent from a file's docstring.

    The first sentence of the module docstring IS the intent.
    If it contains action words (fix, add, build, refactor),
    that's the operator's trace.
    """
    try:
        text = py.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''

    import ast as _ast
    try:
        tree = _ast.parse(text)
        ds = _ast.get_docstring(tree)
        if not ds:
            return ''
    except SyntaxError:
        return ''

    # Get first meaningful line
    for line in ds.split('\n'):
        line = line.strip()
        if not line or line.startswith(('Args:', 'Returns:', '---')):
            continue
        # Strip filename prefix
        if ' — ' in line:
            line = line.split(' — ', 1)[1]
        return line.rstrip('.')

    return ''
