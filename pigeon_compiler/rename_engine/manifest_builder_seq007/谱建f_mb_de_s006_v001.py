"""manifest_builder_seq007_deps_extract_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
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
