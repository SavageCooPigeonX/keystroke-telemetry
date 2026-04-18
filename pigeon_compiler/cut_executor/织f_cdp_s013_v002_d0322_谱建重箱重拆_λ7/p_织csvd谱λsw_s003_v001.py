"""织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_strip_wrapper_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 55 lines | ~587 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast

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
