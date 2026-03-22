"""cognitive_reactor_seq014_docstring_patch_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 62 lines | ~563 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import os
import re

def _apply_docstring_patch(
    root: Path, target_file: dict, module_key: str, avg_hes: float, dominant_state: str
) -> str | None:
    """Safely apply a docstring enhancement to a hot-zone file.

    Only modifies the module-level docstring (first triple-quoted string).
    Adds a COGNITIVE NOTE about the detected load pattern.
    Stages the file change (does NOT commit). Returns path of patched file.
    Safety: never modifies logic code; bails out if file structure is unexpected.
    """
    import ast as _ast
    fp = root / target_file['path']
    if not fp.exists():
        return None
    try:
        source = fp.read_text('utf-8')
        tree = _ast.parse(source)
    except Exception:
        return None

    # Only patch if there's an existing module docstring
    existing_doc = _ast.get_docstring(tree)
    if not existing_doc:
        return None

    # Build the cognitive note to append
    note = (
        f'\n\nCOGNITIVE NOTE (auto-added by reactor): This module triggered '
        f'{FRUSTRATION_STREAK * 2}+ high-load flushes '
        f'(avg_hes={avg_hes:.3f}, state={dominant_state}). '
        f'Consider simplifying its public interface or adding examples.'
    )

    # Only add if not already present
    if 'COGNITIVE NOTE' in existing_doc:
        return None

    # Find the docstring in source and append to it
    # Locate the closing triple-quote of the module docstring
    new_doc = existing_doc + note
    # Replace first occurrence of the original docstring text
    old_doc_escaped = existing_doc.replace('\\', '\\\\').replace('\n', '\n')
    # Simple approach: find end of first docstring block
    for quote in ('"""', "'''"):
        start = source.find(quote)
        if start == -1:
            continue
        end = source.find(quote, start + 3)
        if end == -1:
            continue
        old_block = source[start:end + 3]
        new_block = quote + new_doc + quote
        new_source = source[:start] + new_block + source[end + 3:]
        fp.write_text(new_source, encoding='utf-8')
        return str(fp.relative_to(root))

    return None
