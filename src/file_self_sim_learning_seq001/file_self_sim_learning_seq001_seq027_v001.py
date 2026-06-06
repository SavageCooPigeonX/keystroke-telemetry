"""file_self_sim_learning_seq001_seq027_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from pathlib import Path
from typing import Any
import re

def _proposed_split_children(root: Path, rel: str) -> list[dict[str, str]]:
    path = root / rel
    text = ""
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
    symbols = re.findall(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.MULTILINE)
    stem = _stem_key(rel)
    parent = str(Path(rel).parent).replace("\\", "/")
    if parent == ".":
        parent = "src"
    buckets = [
        ("core", "pure helpers and constants"),
        ("routing", "intent routing and orchestration entrypoints"),
        ("validation", "compile/test guards and 10Q checks"),
        ("io", "log, file, email, or external side effects"),
    ]
    children = []
    for label, role in buckets:
        children.append({
            "path": f"{parent}/{stem}_{label}_seq001_v001.py",
            "role": role,
            "seed_symbols": ", ".join(symbols[:4]) if symbols else "derive from AST during split plan",
        })
    children.append({
        "path": rel,
        "role": "facade preserving current imports while child files take responsibility",
        "seed_symbols": "re-export stable public API",
    })
    return children


def _split_file_quote(rel: str, size: dict[str, Any], tests: list[str]) -> str:
    name = Path(rel).name
    if tests:
        return f"{name}: I am {size.get('line_count')} lines; bring the tests and I will discuss moving out."
    return f"{name}: I am {size.get('line_count')} lines and somehow expected to pack my own boxes without a test witness."
