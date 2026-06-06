"""file_self_sim_learning_seq001_seq036_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
import re

def _file_key_resolver(root: Path) -> dict[str, str]:
    resolver = {}
    for rel in _scan_repo_files(root):
        stem = _stem_key(rel)
        resolver[stem] = rel
        resolver[Path(rel).stem] = rel
    return resolver


def _resolve_file_key(root: Path, file_key: str) -> str:
    target = _stem_key(file_key)
    for rel in _scan_repo_files(root):
        stem = _stem_key(rel)
        if stem == target or Path(rel).stem.startswith(file_key):
            return rel
    return ""


def _scan_repo_files(root: Path) -> list[str]:
    patterns = [
        "*.py",
        "*.md",
        "src/**/*.py",
        "client/**/*.py",
        "test*.py",
        "tests/**/*.py",
        "docs/**/*.md",
        "src/**/MANIFEST.md",
        ".github/copilot-instructions.md",
    ]
    files = []
    for pattern in patterns:
        for path in root.glob(pattern):
            rel = path.relative_to(root).as_posix()
            if "/__pycache__/" in rel or rel.startswith("logs/"):
                continue
            files.append(rel)
    return _dedupe(files)


def _candidate_allowed(root: Path, rel: str) -> bool:
    suffix = Path(rel).suffix.lower()
    if suffix not in {".py", ".md"}:
        return False
    if rel.startswith("logs/") or "/__pycache__/" in rel:
        return False
    return (root / rel).exists()
