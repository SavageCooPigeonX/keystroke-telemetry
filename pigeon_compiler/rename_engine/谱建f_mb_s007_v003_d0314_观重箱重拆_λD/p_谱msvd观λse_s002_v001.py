"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_scan_extract_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import re

def _extract_docstring_first_line(text: str, filename: str) -> str:
    """Extract the first line of the module docstring."""
    try:
        tree = ast.parse(text)
        ds = ast.get_docstring(tree)
        if ds:
            first = ds.strip().split('\n')[0].strip()
            # If docstring starts with "filename.py — description",
            # extract just the description (the intent)
            if ' — ' in first:
                first = first.split(' — ', 1)[1].strip()
            elif ' - ' in first:
                parts = first.split(' - ', 1)
                if len(parts[0].split()) <= 4:
                    first = parts[1].strip()
            if len(first) > 80:
                first = first[:77] + '...'
            return first
    except SyntaxError:
        pass
    # Fallback: infer from filename
    stem = Path(filename).stem
    clean = re.sub(r'_seq\d+_v\d+', '', stem).replace('_', ' ').strip()
    return clean.capitalize() if clean else filename


def _extract_seq(filename: str) -> str:
    """Extract seq number from pigeon filename."""
    m = re.search(r'_seq(\d+)', filename)
    return m.group(1) if m else ''


def _extract_exports(text: str) -> list[str]:
    """Extract public class/function/constant names from a module."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    names = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            names.append(node.name)
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            names.append(f'{node.name}()')
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif node.target:
                targets = [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    names.append(t.id)
    return names


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


def _parse_pigeon_header(text: str) -> dict:
    """Extract pigeon metadata from the # ── pigeon ── header block."""
    info = {}
    for line in text.splitlines()[:20]:
        line = line.strip().lstrip('#').strip()
        if line.startswith('SEQ:'):
            m = re.search(r'VER:\s*(v\d+)', line)
            if m:
                info['ver'] = m.group(1)
            m2 = re.search(r'~([\d,]+)\s*tokens', line)
            if m2:
                info['tokens'] = int(m2.group(1).replace(',', ''))
        elif line.startswith('LAST:'):
            info['last'] = line.split('LAST:', 1)[1].strip()
        elif line.startswith('SESSIONS:'):
            m = re.search(r'SESSIONS:\s*(\d+)', line)
            if m:
                info['sessions'] = int(m.group(1))
        elif line.startswith('INTENT:'):
            info['intent'] = line.split('INTENT:', 1)[1].strip()
    # Also check @pigeon comment for role
    for line in text.splitlines()[:5]:
        if line.startswith('# @pigeon:'):
            m = re.search(r'role=(\w+)', line)
            if m:
                info['role'] = m.group(1)
    return info


def _extract_signatures(text: str) -> list[str]:
    """Extract public function signatures with type hints."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    sigs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_'):
                continue
            sig = _format_signature(node)
            sigs.append(sig)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith('_') and item.name != '__init__':
                        continue
                    sig = _format_signature(item, class_name=node.name)
                    sigs.append(sig)
    return sigs


def _extract_classes(text: str) -> list[dict]:
    """Extract class definitions with methods and bases."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            bases = [ast.unparse(b) for b in node.bases] if node.bases else []
            decorators = []
            for d in node.decorator_list:
                try:
                    decorators.append(ast.unparse(d))
                except Exception:
                    pass
            methods = [m.name for m in node.body
                       if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and not m.name.startswith('_')]
            classes.append({
                'name': node.name,
                'bases': bases,
                'decorators': decorators,
                'methods': methods,
                'lines': (node.end_lineno or node.lineno) - node.lineno + 1,
            })
    return classes


def _extract_constants(text: str) -> list[dict]:
    """Extract module-level public constants with their values."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    consts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    try:
                        val_str = ast.unparse(node.value)
                        if len(val_str) > 80:
                            val_str = val_str[:77] + '...'
                    except Exception:
                        val_str = '...'
                    consts.append({'name': t.id, 'value': val_str})
    return consts


def _extract_code_markers(text: str) -> list[dict]:
    """Extract TODO/FIXME/HACK/NOTE markers from comments."""
    markers = []
    for i, line in enumerate(text.splitlines(), 1):
        m = _MARKER_RE.search(line)
        if m:
            tag = m.group(1).upper()
            rest = line[m.end():].strip().lstrip(':').strip()
            if len(rest) > 60:
                rest = rest[:57] + '...'
            markers.append({'tag': tag, 'line': i, 'text': rest})
    return markers
