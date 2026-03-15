"""run_clean_split_helpers_seq011_v001.py — Helpers for run_clean_split.

Decomposition, init writer, manifest writer, seq numbering.
Split from main runner to stay under 50 lines.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v004 | 59 lines | ~570 tokens
# DESC:   helpers_for_run_clean_split
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast, re
from pathlib import Path
from datetime import datetime
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED


def decompose_oversized(source_file: Path, em: dict) -> tuple:
    """DeepSeek-decompose functions >50 lines. Returns (path, cost)."""
    from pigeon_compiler.cut_executor.func_decomposer_seq008_v004_d0315__decompose_oversized_functions_via_deepseek_lc_verify_pigeon_plugin import (
        find_oversized, decompose_function)
    from pigeon_compiler.cut_executor.source_slicer_seq002_v004_d0315__extract_functions_constants_from_source_lc_verify_pigeon_plugin import (
        _node_name, _node_range)

    big = find_oversized(em)
    if not big:
        return source_file, 0.0

    print(f"  Decomposing {len(big)} oversized functions...")
    src = source_file.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)

    replacements, cost = [], 0.0
    for fi in sorted(big, key=lambda f: -f["start_line"]):
        for node in ast.iter_child_nodes(tree):
            if _node_name(node) == fi["name"]:
                s, e = _node_range(node, lines)
                fsrc = "".join(lines[s:e])
                print(f"    {fi['name']}() ({fi['line_count']}→≤30 each)")
                try:
                    code = decompose_function(fsrc, fi["name"], fi["line_count"])
                    replacements.append((s, e, code))
                    cost += 0.002
                except Exception as ex:
                    print(f"    ⚠️ {fi['name']}: {ex}")
                break

    if not replacements:
        return source_file, cost

    for s, e, new in replacements:
        lines[s:e] = [new + "\n\n"]

    out = source_file.parent / f".{source_file.stem}_decomposed.py"
    out.write_text("".join(lines), encoding="utf-8")
    return out, cost
