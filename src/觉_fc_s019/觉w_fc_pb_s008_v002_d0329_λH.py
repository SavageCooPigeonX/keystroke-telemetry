"""file_consciousness_seq019_profile_builder_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

import ast
import re

def _build_func_profile(node, source: str, local_fns: set) -> dict:
    """Build consciousness for a single function node."""
    body_src = ast.get_source_segment(source, node) or ''
    lines = body_src.splitlines()

    return {
        'function': node.name,
        'line_range': [node.lineno, node.end_lineno or node.lineno],
        'i_am': _derive_purpose(node, lines),
        'i_want': _derive_dependencies(node, local_fns),
        'i_give': _derive_exports(node),
        'i_fear': _derive_fears(node, lines),
        'i_love': _derive_loves(node, lines),
        'personality': _classify_personality(node, local_fns),
        'flags': _count_flags(lines),
    }
