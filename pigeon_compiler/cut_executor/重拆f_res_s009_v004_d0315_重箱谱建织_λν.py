"""resplit_seq009_v001.py — Deterministic AST bin-packing re-splitter.

Takes a folder of Python files. For any file >PIGEON_MAX lines,
splits it by AST into multiple files, each ≤PIGEON_MAX.
No AI needed — pure math.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v004 | 89 lines | ~845 tokens
# DESC:   deterministic_ast_bin_packing_re
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast
from pathlib import Path
from pigeon_compiler.cut_executor.重助p_rehe_s011_v004_d0315_重箱重拆切_λν import (
    line_count, node_name, collect_imports)
from pigeon_compiler.cut_executor.重箱f_rebi_s010_v004_d0315_重拆谱建织_λν import (
    bin_pack, write_splits)
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED, FILE_OVERHEAD, is_excluded


def scan_violations(folder: Path) -> list[Path]:
    """Return list of .py files exceeding PIGEON_MAX that can be split.

    Files with a single class as their only content are skipped —
    classes are indivisible at the AST level.
    """
    violations = []
    for f in sorted(folder.glob("*.py")):
        if is_excluded(f):
            continue
        if line_count(f) <= PIGEON_MAX:
            continue
        # Skip files that are a single class (can't be split further)
        src = f.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            violations.append(f)
            continue
        top_items = [n for n in ast.iter_child_nodes(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                       ast.ClassDef, ast.Assign))]
        if len(top_items) == 1 and isinstance(top_items[0], ast.ClassDef):
            # Single class — resplitter can't split further.
            # Phase 1b (class_decomposer) should have handled this.
            print(f"    ⚠️ {f.name}: single class still oversized — "
                  "class_decomposer may have missed it")
            continue
        violations.append(f)
    return violations


def resplit_file(file_path: Path) -> list[dict]:
    """Extract top-level items from an oversized file.

    Returns list of {name, source, lines, start} dicts.
    Caller is responsible for bin_pack + write.
    """
    src = file_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    return _extract_items(tree, src)


def _extract_items(tree, source: str) -> list[dict]:
    """Get every top-level item with its source + line count.

    For classes exceeding PIGEON_MAX, the class is kept as a single item
    (classes can't be bin-packed across files), so we don't split them.
    Instead, the caller will write them to their own file even if oversized.
    """
    lines = source.splitlines(keepends=True)
    items = []
    for node in ast.iter_child_nodes(tree):
        name = node_name(node)
        if not name:
            continue
        start = node.lineno - 1
        if hasattr(node, "decorator_list") and node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        end = node.end_lineno or node.lineno
        if end < len(lines) and lines[end].strip() == "":
            end += 1
        lc = end - start
        items.append({
            "name": name, "source": "".join(lines[start:end]),
            "lines": lc, "start": start,
            "is_class": isinstance(node, ast.ClassDef),
        })
    return items
