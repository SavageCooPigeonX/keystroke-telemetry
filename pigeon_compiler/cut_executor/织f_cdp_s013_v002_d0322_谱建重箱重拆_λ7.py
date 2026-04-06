"""class_decomposer_seq013_v001.py — Decompose oversized classes via DeepSeek.

For classes >PIGEON_MAX lines, sends a CODING prompt to DeepSeek asking it
to extract methods as standalone module-level functions and keep the class thin.
Returns modified source where the class delegates to extracted functions.
"""

import ast
from pathlib import Path

from pigeon_compiler.pigeon_limits import PIGEON_MAX


def find_oversized_classes(ether_map: dict) -> list:
    """Return classes that exceed PIGEON_MAX lines."""
    return [c for c in ether_map.get("classes", [])
            if (c.get("end_line", 0) - c.get("start_line", 0) + 1) > PIGEON_MAX]


def _build_prompt(class_source: str, class_name: str,
                  line_count: int, context: str = "") -> str:
    """Build a CODING prompt to refactor one large class."""
    ctx_block = (
        f"EXISTING CODE ABOVE THE CLASS (DO NOT REPEAT THIS — it stays in the file):\n\n"
        f"{context}\n\n"
    ) if context else ""
    return (
        "You are the Pigeon Code Compiler. Refactor this oversized class "
        "into a THIN class + standalone module-level functions.\n\n"
        "RULES:\n"
        "- Extract methods that compute or render into STANDALONE module-level functions.\n"
        "  Replace self.xxx references with explicit parameters.\n"
        "- The class keeps: __init__, simple state-management methods,\n"
        "  and delegates to the extracted functions.\n"
        "- Each extracted function MUST be ≤50 lines.\n"
        "- The remaining class MUST be ≤80 lines.\n"
        "- Preserve EXACT behavior — no logic changes.\n"
        "- Extracted functions receive data as parameters, NOT self.\n"
        "- Keep the same class NAME and public API (method signatures unchanged from caller's view).\n"
        "- Private methods like _render, _compute, _format → module-level functions.\n"
        "- Return ONLY valid Python code — NO markdown fences, NO comments like '```python'.\n"
        "- Do NOT re-include imports, constants, or helper functions that exist ABOVE the class.\n"
        "  They already exist in the file. ONLY output the NEW extracted functions\n"
        "  and the refactored thin class.\n"
        "- If extracted functions need imports not already in context, add ONLY those new imports.\n\n"
        + ctx_block
        + f"CLASS TO REFACTOR ({line_count} lines):\n\n"
        f"{class_source}\n\n"
        "Output ONLY:\n"
        "1. Any NEW imports needed by extracted functions (not already above)\n"
        "2. The extracted standalone functions\n"
        "3. The thin class that delegates to them\n"
        "No markdown fences. No duplicate code."
    )


def _call_deepseek(prompt: str) -> str:
    """Call DeepSeek and strip any markdown fences from the response."""
    from pigeon_compiler.integrations.谱p_dsa_s001_v006_d0322_读_λ7 import (
        deepseek_query)

    result = deepseek_query(prompt, max_tokens=8000)
    code = result.get("content", "")
    if code.startswith("```"):
        lines = code.split("\n")
        end = -1 if lines[-1].strip().startswith("```") else len(lines)
        code = "\n".join(lines[1:end])
    return code.strip(), result.get("cost", 0)


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


def _strip_duplicate_defs(new_code: str, existing_code: str) -> str:
    """Remove function/constant defs from new_code that already exist in existing_code."""
    try:
        existing_tree = ast.parse(existing_code)
        existing_names = set()
        for node in ast.iter_child_nodes(existing_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                existing_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                existing_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        existing_names.add(t.id)

        new_tree = ast.parse(new_code)
        new_lines = new_code.splitlines(keepends=True)
        # Collect ranges to remove (duplicate defs)
        remove_ranges = []
        for node in ast.iter_child_nodes(new_tree):
            name = None
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        name = t.id
            # Also strip duplicate import lines
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Keep imports — they're lightweight and may be needed
                continue
            if name and name in existing_names:
                start = node.lineno - 1
                if hasattr(node, 'decorator_list') and node.decorator_list:
                    start = node.decorator_list[0].lineno - 1
                end = node.end_lineno or node.lineno
                if end < len(new_lines) and new_lines[end].strip() == '':
                    end += 1
                remove_ranges.append((start, end))

        if not remove_ranges:
            return new_code

        # Remove ranges in reverse order
        for start, end in sorted(remove_ranges, reverse=True):
            del new_lines[start:end]

        # Also strip duplicate import lines
        result = "".join(new_lines).strip()
        return result
    except SyntaxError:
        return new_code
