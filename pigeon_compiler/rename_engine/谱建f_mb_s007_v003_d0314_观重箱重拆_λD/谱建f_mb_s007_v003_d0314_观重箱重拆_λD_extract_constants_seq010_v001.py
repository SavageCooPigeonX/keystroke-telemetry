"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_constants_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 23 lines | ~219 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_constants(text: str) -> list[dict]:
    """Extract module-level public constants with their values."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    consts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    try:
                        val_str = ast.unparse(node.value)
                        if len(val_str) > 80:
                            val_str = val_str[:77] + '...'
                    except Exception:
                        val_str = '...'
                    consts.append({'name': t.id, 'value': val_str})
    return consts
