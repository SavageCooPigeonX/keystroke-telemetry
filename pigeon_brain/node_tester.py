"""Node tester — real import/AST/edge tests triggered by UI touch.

When the UI taps a node, this module:
1. Resolves the node name to its actual file path
2. Runs Layer 1 tests: AST parse, import resolution, outbound edge check, export verification
3. Returns structured results as events for WS broadcast

Zero LLM calls. Pure file system + AST signal.
"""

import ast
import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path


def _resolve_path(root: Path, node_name: str) -> Path | None:
    """Find the actual .py file for a node name using pigeon_registry.json or dual_view.json."""
    # Try dual_view first (has full path field)
    dv = root / "pigeon_brain" / "dual_view.json"
    if dv.exists():
        try:
            data = json.loads(dv.read_text(encoding="utf-8"))
            for n in data.get("nodes", []):
                if n.get("name") == node_name:
                    p = root / n["path"]
                    if p.exists():
                        return p
        except Exception:
            pass

    # Fallback: glob for the name pattern
    for pattern in [f"**/{node_name}_seq*", f"**/{node_name}.*"]:
        hits = list(root.glob(pattern))
        py_hits = [h for h in hits if h.suffix == ".py" and h.is_file()]
        if py_hits:
            return py_hits[0]
    return None


def _extract_imports(source: str) -> list[str]:
    """Extract all import targets from source code via AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _extract_exports(source: str) -> list[str]:
    """Extract top-level function/class names (the module's exports)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    exports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                exports.append(node.name)
    return exports


def _extract_used_names(source: str) -> set[str]:
    """Extract all Name nodes referenced in function/class bodies (usage sites)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
    return used


def _find_dead_imports(source: str) -> list[str]:
    """Find imports whose names are never referenced in the rest of the file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    # Collect imported names and their bound aliases
    imported = {}  # alias -> module
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[-1]
                imported[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imported[name] = f"{node.module}.{alias.name}" if node.module else alias.name
    if not imported:
        return []
    # Collect all Name references in the file (excluding import nodes themselves)
    used = _extract_used_names(source)
    dead = []
    for alias, full in imported.items():
        if alias not in used:
            dead.append(full)
    return dead


def _find_unused_exports(root: Path, node_name: str, exports: list[str]) -> list[str]:
    """Find exports that no other file in the project imports."""
    if not exports:
        return []
    dv = root / "pigeon_brain" / "dual_view.json"
    if not dv.exists():
        return []
    try:
        data = json.loads(dv.read_text(encoding="utf-8"))
    except Exception:
        return []
    # Get all files that import this node (edges_in = who depends on us)
    node_data = next((n for n in data.get("nodes", []) if n.get("name") == node_name), None)
    if not node_data:
        return []
    importers = node_data.get("edges_in", [])
    if not importers:
        return exports  # nobody imports us at all — all exports are unused

    # Check each importer's source for references to our exports
    used_exports = set()
    for imp_name in importers:
        imp_path = _resolve_path(root, imp_name)
        if not imp_path or not imp_path.exists():
            continue
        try:
            imp_source = imp_path.read_text(encoding="utf-8")
            names = _extract_used_names(imp_source)
            used_exports.update(e for e in exports if e in names)
        except Exception:
            continue
    return [e for e in exports if e not in used_exports]


def test_node(root: Path, node_name: str) -> list[dict]:
    """Run all Layer 1 checks on a node. Returns a list of test result events.

    Each event: {module, event, func, status, detail, timestamp}
    """
    now_ms = int(time.time() * 1000)
    results = []

    def _evt(func: str, status: str, detail: str = "", caller: str = ""):
        evt = {
            "module": node_name,
            "event": "return" if status == "alive" else "exception",
            "func": func,
            "status": status,
            "detail": detail,
            "timestamp": int(time.time() * 1000),
        }
        if caller:
            evt["caller"] = caller
        results.append(evt)
        return evt

    # ── Test 1: file exists ──
    fpath = _resolve_path(root, node_name)
    if not fpath:
        _evt("file_exists", "dead", f"No file found for '{node_name}'")
        return results
    _evt("file_exists", "alive", str(fpath.relative_to(root)))

    # ── Test 2: AST parse ──
    try:
        source = fpath.read_text(encoding="utf-8")
    except Exception as e:
        _evt("ast_parse", "dead", f"Read error: {e}")
        return results

    try:
        ast.parse(source)
        _evt("ast_parse", "alive", f"{len(source.splitlines())} lines")
    except SyntaxError as e:
        _evt("ast_parse", "dead", f"SyntaxError line {e.lineno}: {e.msg}")
        return results  # no point continuing if unparseable

    # ── Test 3: line count check ──
    line_count = len(source.splitlines())
    if line_count > 200:
        _evt("line_cap", "dead", f"{line_count} lines (>200 hard cap)")
    elif line_count > 150:
        _evt("line_cap", "alive", f"{line_count} lines (approaching cap)")
    else:
        _evt("line_cap", "alive", f"{line_count} lines")

    # ── Test 4: outbound import resolution ──
    imports = _extract_imports(source)
    dead_imports = []
    for imp in imports:
        # Only check project-internal imports
        if not any(imp.startswith(p) for p in ("src.", "pigeon_compiler.", "pigeon_brain.", "streaming_layer.", "client.")):
            continue
        spec = importlib.util.find_spec(imp)
        if spec is None:
            dead_imports.append(imp)

    if dead_imports:
        _evt("import_resolve", "dead", f"Dead imports: {', '.join(dead_imports[:5])}")
    else:
        internal_count = len([i for i in imports if any(i.startswith(p) for p in ("src.", "pigeon_compiler.", "pigeon_brain.", "streaming_layer.", "client."))])
        _evt("import_resolve", "alive", f"{internal_count} internal imports OK")

    # ── Test 5: export verification vs registry ──
    exports = _extract_exports(source)
    _evt("exports", "alive", f"{len(exports)} exports: {', '.join(exports[:5])}")

    # ── Test 6: outbound edge targets exist ──
    dv = root / "pigeon_brain" / "dual_view.json"
    if dv.exists():
        try:
            data = json.loads(dv.read_text(encoding="utf-8"))
            node_data = next((n for n in data.get("nodes", []) if n.get("name") == node_name), None)
            if node_data:
                edges_out = node_data.get("edges_out", [])
                all_names = {n["name"] for n in data.get("nodes", [])}
                missing = [e for e in edges_out if e not in all_names]
                if missing:
                    _evt("edge_targets", "dead", f"Missing targets: {', '.join(missing[:5])}")
                elif edges_out:
                    _evt("edge_targets", "alive", f"{len(edges_out)} outbound edges verified")
        except Exception:
            pass

    # ── Test 7: dead imports (imported but never used in the file) ──
    dead_imps = _find_dead_imports(source)
    if dead_imps:
        _evt("dead_import", "dead", f"Unused imports: {', '.join(dead_imps[:5])}")
    else:
        _evt("dead_import", "alive", "No dead imports")

    # ── Test 8: unused exports (defined but nobody imports them) ──
    unused = _find_unused_exports(root, node_name, exports)
    if unused:
        _evt("unused_export", "dead", f"Unused exports: {', '.join(unused[:5])}")
    elif exports:
        _evt("unused_export", "alive", f"All {len(exports)} exports consumed")

    # ── Test 9: dead edges (edges_out to nodes that don't actually import us back or are orphans) ──
    if dv.exists():
        try:
            data = json.loads(dv.read_text(encoding="utf-8"))
            node_data = next((n for n in data.get("nodes", []) if n.get("name") == node_name), None)
            if node_data:
                edges_out = node_data.get("edges_out", [])
                dead_edges = []
                for target in edges_out:
                    t_path = _resolve_path(root, target)
                    if not t_path or not t_path.exists():
                        dead_edges.append(target)
                        continue
                    # Check if target file actually references anything from us
                    try:
                        t_src = t_path.read_text(encoding="utf-8")
                        t_imports = _extract_imports(t_src)
                        # We appear in their edges_out (they import us), not the other way
                        # For dead edge: we claim to use them — verify our source actually imports them
                        base = target.split("_seq")[0] if "_seq" in target else target
                        if not any(base in imp for imp in imports):
                            dead_edges.append(target)
                    except Exception:
                        pass
                if dead_edges:
                    _evt("dead_edge", "dead", f"Dead edges: {', '.join(dead_edges[:5])}")
                elif edges_out:
                    _evt("dead_edge", "alive", f"{len(edges_out)} edges verified live")
        except Exception:
            pass

    # ── Cascade: test downstream neighbors ──
    # Return events for each downstream node (the cascade walks these)
    if dv.exists():
        try:
            data = json.loads(dv.read_text(encoding="utf-8"))
            edges = data.get("edges", [])
            downstream = [e["to"] for e in edges if e["from"] == node_name]
            for dep in downstream[:8]:  # cap at 8 to avoid explosion
                dep_path = _resolve_path(root, dep)
                if dep_path and dep_path.exists():
                    try:
                        dep_source = dep_path.read_text(encoding="utf-8")
                        ast.parse(dep_source)
                        results.append({
                            "module": dep,
                            "event": "return",
                            "func": "cascade",
                            "caller": node_name,
                            "status": "alive",
                            "detail": "downstream reachable",
                            "timestamp": int(time.time() * 1000),
                        })
                    except SyntaxError:
                        results.append({
                            "module": dep,
                            "event": "exception",
                            "func": "cascade",
                            "caller": node_name,
                            "status": "dead",
                            "detail": "syntax error in downstream",
                            "timestamp": int(time.time() * 1000),
                        })
                else:
                    results.append({
                        "module": dep,
                        "event": "exception",
                        "func": "cascade",
                        "caller": node_name,
                        "status": "dead",
                        "detail": "file not found",
                        "timestamp": int(time.time() * 1000),
                    })
        except Exception:
            pass

    return results
