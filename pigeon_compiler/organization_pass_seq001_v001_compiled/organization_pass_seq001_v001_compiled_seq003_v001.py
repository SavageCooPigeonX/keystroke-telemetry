"""organization_pass_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .organization_pass_seq001_v001_compiled_seq006_v001 import _folder_of
from .organization_pass_seq001_v001_compiled_seq006_v001 import _module_name
from .organization_pass_seq001_v001_compiled_seq006_v001 import _read_text
from .organization_pass_seq001_v001_compiled_seq007_v001 import FileInfo
from pathlib import Path
import ast
import re

def _file_info(root: Path, path: Path, module_index: dict[str, str]) -> FileInfo:
    rel = path.relative_to(root).as_posix()
    folder = _folder_of(rel)
    text = _read_text(path)
    imports: list[str] = []
    parse_error = ""
    try:
        tree = ast.parse(text)
        imports = _project_imports(tree, module_index)
    except SyntaxError as exc:
        parse_error = f"{exc.__class__.__name__}: {exc.msg}"
    return FileInfo(
        rel=rel,
        folder=folder,
        module=_module_name(root, path),
        line_count=text.count("\n") + (1 if text else 0),
        imports=tuple(imports),
        parse_error=parse_error,
    )


def _project_imports(tree: ast.AST, module_index: dict[str, str]) -> list[str]:
    imports: list[str] = []
    known_modules = set(module_index)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = _resolve_import(alias.name, known_modules)
                if target:
                    imports.append(module_index[target])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            base = node.module or ""
            for alias in node.names:
                target = _resolve_import(f"{base}.{alias.name}", known_modules) or _resolve_import(base, known_modules)
                if target:
                    imports.append(module_index[target])
    return tuple(dict.fromkeys(imports))


def _resolve_import(name: str, known_modules: set[str]) -> str:
    parts = name.split(".")
    for size in range(len(parts), 0, -1):
        candidate = ".".join(parts[:size])
        if candidate in known_modules:
            return candidate
    return ""
