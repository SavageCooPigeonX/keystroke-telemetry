"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_signatures_only_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 25 lines | ~247 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_signatures(text: str) -> list[str]:
    """Extract public function signatures with type hints."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    sigs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_'):
                continue
            sig = _format_signature(node)
            sigs.append(sig)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith('_') and item.name != '__init__':
                        continue
                    sig = _format_signature(item, class_name=node.name)
                    sigs.append(sig)
    return sigs
