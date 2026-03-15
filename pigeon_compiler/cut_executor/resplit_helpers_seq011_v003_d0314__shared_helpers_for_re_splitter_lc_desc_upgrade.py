"""resplit_helpers_seq011_v001.py — Shared helpers for re-splitter modules."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v003 | 52 lines | ~437 tokens
# DESC:   shared_helpers_for_re_splitter
# INTENT: desc_upgrade
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
from pathlib import Path


def line_count(file_path: Path) -> int:
    """Count lines in a file."""
    return len(file_path.read_text(encoding="utf-8").splitlines())


def node_name(node) -> str | None:
    """Get name of a top-level AST node."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name
    if isinstance(node, ast.ClassDef):
        return node.name
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                return t.id
    return None


def collect_imports(source: str) -> list[str]:
    """Get all top-level import lines from source as raw strings."""
    tree = ast.parse(source)
    lines = source.splitlines()
    imps = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imps.append(lines[node.lineno - 1])
    return sorted(set(imps))


def filter_imports(body: str, all_imports: list[str]) -> list[str]:
    """Keep only imports whose names appear in body."""
    needed = []
    for imp in all_imports:
        # Extract names from import line
        for token in imp.replace(",", " ").split():
            if token in body and token not in (
                "import", "from", "as"):
                needed.append(imp)
                break
    return needed


def assemble_file(fname: str, imports: list[str], body: str) -> str:
    """Build a complete Pigeon file: docstring + imports + body."""
    doc = f'"""{fname} — Pigeon-extracted by compiler."""\n'
    imp = "\n".join(imports) + "\n" if imports else ""
    return doc + imp + "\n" + body.rstrip() + "\n"
