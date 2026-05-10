"""file_writer_seq003_v001.py — Write new Pigeon-compliant files from cut plan.

Creates each file with: docstring, imports, extracted code.
Resolves which imports each file actually needs.
"""

import ast
from pathlib import Path
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED


def write_cut_files(plan: dict, sliced: dict, source_path: Path,
                    target_dir: Path, dry_run: bool = False) -> list:
    """Write all cut files. Returns list of {path, lines, status}."""
    target_dir.mkdir(parents=True, exist_ok=True)
    source_text = source_path.read_text(encoding='utf-8')
    original_imports = _collect_imports(source_text)
    symbol_modules = _symbol_module_map(plan)
    results = []
    for cut in plan["cuts"]:
        fname = cut["new_file"]
        names = cut.get("functions", []) + cut.get("constants", [])
        names += cut.get("classes", [])  # class extraction
        names += cut.get("contents", [])  # v1 compat
        body = _build_body(names, sliced)
        needed = _resolve_imports(body, original_imports, plan, cut, symbol_modules)
        content = _assemble(fname, needed, body)
        out = target_dir / fname
        lc = content.count('\n') + 1
        if lc <= PIGEON_RECOMMENDED:
            status = "OK"
        elif lc <= PIGEON_MAX:
            status = f"WARN ({lc})"
        else:
            status = f"OVER ({lc})"
        if not dry_run:
            out.write_text(content, encoding='utf-8')
        results.append({"file": fname, "lines": lc, "status": status})
    return results


def _build_body(names, sliced):
    parts = [sliced[n] for n in names if n in sliced]
    return "\n".join(parts)


def _resolve_imports(body, orig_imports, plan, cut, symbol_modules=None):
    """Figure out which original and sibling imports this file actually uses."""
    needed = []
    for imp in orig_imports:
        for name in imp["names"]:
            if name in body:
                needed.append(imp["line"])
                break
    needed.extend(_resolve_internal_imports(body, cut, symbol_modules or {}))
    return sorted(set(needed))


def _symbol_module_map(plan: dict) -> dict[str, str]:
    """Map every planned top-level symbol to the module that will own it."""
    out = {}
    for cut in plan.get("cuts", []):
        module = Path(cut.get("new_file", "")).stem
        names = []
        for key in ("functions", "constants", "classes", "contents"):
            names.extend(cut.get(key, []) or [])
        for name in names:
            if name:
                out[str(name)] = module
    return out


def _resolve_internal_imports(body: str, cut: dict, symbol_modules: dict[str, str]) -> list[str]:
    """Add imports for extracted sibling helpers referenced by this cut."""
    if not symbol_modules:
        return []
    current_module = Path(cut.get("new_file", "")).stem
    current_names = set()
    for key in ("functions", "constants", "classes", "contents"):
        current_names.update(cut.get(key, []) or [])
    used = _used_names(body)
    lines = []
    for name in sorted(used):
        module = symbol_modules.get(name)
        if not module or module == current_module or name in current_names:
            continue
        lines.append(f"from .{module} import {name}")
    return lines


def _used_names(body: str) -> set[str]:
    """Collect loaded names from an extracted body."""
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return set()
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    return used


def _collect_imports(source: str) -> list:
    tree = ast.parse(source)
    imps = []
    lines = source.splitlines()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.asname or a.name for a in node.names]
            else:
                names = [a.name for a in node.names]
            # Capture full multi-line import (lineno to end_lineno)
            full_line = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            imps.append({"names": names, "line": full_line})
    return imps


def _assemble(fname, import_lines, body):
    stem = Path(fname).stem
    doc = f'"""{fname} — Auto-extracted by Pigeon Compiler."""\n'
    imp_block = "\n".join(import_lines) + "\n" if import_lines else ""
    return doc + imp_block + "\n" + body.rstrip() + "\n"
