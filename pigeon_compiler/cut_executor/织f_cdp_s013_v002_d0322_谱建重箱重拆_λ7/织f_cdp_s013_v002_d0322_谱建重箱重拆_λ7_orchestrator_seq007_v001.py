"""织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_orchestrator_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 51 lines | ~550 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from pigeon_compiler.pigeon_limits import PIGEON_MAX
from .织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_find_classes_seq004_v001 import find_oversized_classes
import ast

def decompose_oversized_classes(source_file: Path, em: dict):
    """Refactor classes >PIGEON_MAX via DeepSeek. Returns (path, cost)."""
    from pigeon_compiler.cut_executor.切p_ss_s002_v004_d0315_重箱重助重拆_λν import (
        _node_name, _node_range)

    big = find_oversized_classes(em)
    if not big:
        return source_file, 0.0

    print(f"  Decomposing {len(big)} oversized class(es)...")
    src = source_file.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)

    replacements = []
    total_cost = 0.0
    for ci in sorted(big, key=lambda c: -(c.get("end_line", 0))):
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name == ci["name"]:
                s, e = _node_range(node, lines)
                csrc = "".join(lines[s:e])
                lc = e - s
                # Context = everything before the class (imports, constants, helpers)
                context = "".join(lines[:s]).strip()
                print(f"    {ci['name']} ({lc} lines → thin class + functions)")
                prompt = _build_prompt(csrc, ci["name"], lc, context)
                code, cost = _call_deepseek(prompt)
                total_cost += cost
                if code and len(code.splitlines()) > 10:
                    replacements.append((s, e, code))
                else:
                    print(f"    ⚠️ DeepSeek returned insufficient code, skipping")
                break

    if not replacements:
        return source_file, total_cost

    for s, e, new in sorted(replacements, key=lambda r: -r[0]):
        # Strip any duplicate imports/constants DeepSeek may have re-included
        new_clean = _strip_duplicate_defs(new, "".join(lines[:s]))
        lines[s:e] = [new_clean + "\n\n"]

    out = source_file.parent / f".{source_file.stem}_class_decomposed.py"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"    Wrote decomposed source → {out.name}")
    return out, total_cost
