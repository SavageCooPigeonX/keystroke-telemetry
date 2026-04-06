"""file_consciousness_seq019_derivation_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import ast
import json
import re

def _derive_purpose(node, lines: list[str]) -> str:
    """i_am: What this function does (from docstring or name heuristics)."""
    ds = ast.get_docstring(node)
    if ds:
        return ds.split('\n')[0].strip()[:120]
    # Fallback: convert function name to readable description
    name = node.name.lstrip('_')
    return name.replace('_', ' ')


def _derive_fears(node, lines: list[str]) -> list[str]:
    """i_fear: Failure modes — missing files, silent errors, regex deps."""
    fears = []
    body_text = '\n'.join(lines)

    # Bare except / broad exception handling = hiding errors
    for child in ast.walk(node):
        if isinstance(child, ast.ExceptHandler):
            if child.type is None:
                fears.append('bare except hides errors')
            elif isinstance(child.type, ast.Name) and child.type.id == 'Exception':
                # Check if body is just pass/continue
                if any(isinstance(b, (ast.Pass, ast.Continue)) for b in child.body):
                    fears.append('swallowed exception')

    # Regex usage = fragile format dependency
    if 're.search' in body_text or 're.match' in body_text or 're.findall' in body_text:
        fears.append('regex format dependency')

    # Path.exists() check = file might not exist
    if '.exists()' in body_text:
        fears.append('file may not exist')

    # Empty return on error path = silent failure
    for child in ast.walk(node):
        if isinstance(child, ast.Return):
            if isinstance(child.value, (ast.List, ast.Tuple, ast.Dict)):
                if not child.value.elts if hasattr(child.value, 'elts') else not child.value.keys:
                    fears.append('returns empty on failure (silent)')

    return list(dict.fromkeys(fears))[:5]


def _derive_loves(node, lines: list[str]) -> list[str]:
    """i_love: What this function relies on being stable."""
    loves = []
    body_text = '\n'.join(lines)

    if 'encoding=' in body_text:
        loves.append('consistent file encoding')
    if '.splitlines()' in body_text or '.split(' in body_text:
        loves.append('stable text format')
    if 'json.loads' in body_text or 'json.load' in body_text:
        loves.append('valid JSON input')
    if '.glob(' in body_text or '.rglob(' in body_text:
        loves.append('predictable directory structure')
    if 'subprocess' in body_text:
        loves.append('external tool availability')
    return loves[:4]
