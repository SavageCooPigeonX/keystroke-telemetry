"""folder_context_coupling_seq001_v001_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq008_v001 import _path_identity_tokens
from .folder_context_coupling_seq001_v001_compiled_seq008_v001 import _read_prefix
from .folder_context_coupling_seq001_v001_compiled_seq008_v001 import _split_identity_text
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import AST_IDENTITY_FILE_CAP
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import _IDENTITY_STOPWORDS
from collections import defaultdict
from pathlib import Path
from typing import Any
import ast

def _folder_identity(root: Path, folder: str, local_files: list[str]) -> dict[str, Any]:
    token_scores: dict[str, int] = defaultdict(int)
    path_tokens = _path_identity_tokens(folder)
    for token in path_tokens:
        token_scores[token] += 12

    manifest = root / ("MANIFEST.md" if folder == "." else f"{folder}/MANIFEST.md")
    if manifest.exists():
        for token in _split_identity_text(_read_prefix(manifest, 2400)):
            token_scores[token] += 2

    ast_sources = 0
    for rel in [row for row in local_files if row.endswith(".py")][:AST_IDENTITY_FILE_CAP]:
        try:
            tree = ast.parse(_read_prefix(root / rel, 12000))
        except Exception:
            continue
        ast_sources += 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for token in _split_identity_text(node.name):
                    token_scores[token] += 3
        doc = ast.get_docstring(tree) or ""
        for token in _split_identity_text(doc[:1200]):
            token_scores[token] += 1

    scored_tokens = [
        token
        for token, _score in sorted(token_scores.items(), key=lambda item: (-item[1], item[0]))
        if token not in _IDENTITY_STOPWORDS
    ]
    tokens = list(dict.fromkeys(path_tokens + scored_tokens))[:4]
    if not tokens:
        tokens = ["folder", "context"]
    label = _operator_label(path_tokens if folder in {"", ".", "src"} else tokens)
    return {
        "operator_label": label,
        "identity_tokens": tokens,
        "identity_source": "path+manifest+ast" if ast_sources else "path+manifest",
    }


def _operator_label(tokens: list[str]) -> str:
    title = " ".join(token.replace("_", " ").title() for token in tokens[:3])
    return f"{title}-inator"
