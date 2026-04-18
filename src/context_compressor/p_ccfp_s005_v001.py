"""context_compressor_seq001_v001_file_processor_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 29 lines | ~193 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast

def compress_file(filepath):
    try:
        text = filepath.read_text('utf-8', errors='ignore')
    except Exception:
        return None, 0, 0

    orig_tokens = _approx_tokens(text)
    cleaned = _strip_comments(text)

    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return None, orig_tokens, 0

    _strip_docstrings(tree)
    _strip_type_annotations(tree)
    ast.fix_missing_locations(tree)

    try:
        compressed = ast.unparse(tree)
    except Exception:
        return None, orig_tokens, 0

    compressed = _collapse_blanks(compressed)
    new_tokens = _approx_tokens(compressed)
    return compressed, orig_tokens, new_tokens
