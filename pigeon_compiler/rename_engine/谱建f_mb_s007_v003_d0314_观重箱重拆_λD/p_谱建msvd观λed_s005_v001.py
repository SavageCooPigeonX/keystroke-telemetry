"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_deps_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 23 lines | ~231 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_deps(text: str, folder_name: str) -> list[str]:
    """Extract intra-project import targets (module stems)."""
    deps = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return deps
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            # Only track project-internal imports
            if any(mod.startswith(p) for p in ('src.', 'pigeon_compiler.', 'streaming_layer.')):
                # Extract the final module stem
                leaf = mod.rsplit('.', 1)[-1]
                # Strip pigeon suffixes for readability
                short = re.sub(r'_seq\d+.*', '', leaf)
                if short and short not in deps:
                    deps.append(short)
    return deps
