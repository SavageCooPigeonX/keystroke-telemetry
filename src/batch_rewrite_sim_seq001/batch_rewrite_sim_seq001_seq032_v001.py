"""batch_rewrite_sim_seq001_seq032_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq033_v001 import _stem_key
from .batch_rewrite_sim_seq001_seq034_v001 import VERBS
from pathlib import Path
import os
import re
import subprocess

def _referenced_by(root: Path, stem: str, self_rel: str) -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "grep", "-l", stem, "--", "*.py"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    out = []
    for line in result.stdout.splitlines():
        rel = _clean_rel_path(line)
        if rel and rel != self_rel and (root / rel).exists():
            out.append(rel)
    return out[:20]


def _clean_rel_path(value: str) -> str:
    text = value.strip().strip('"').replace("\\", "/")
    return text if text and ".." not in Path(text).parts else ""


def _resolve_stem(root: Path, name: str) -> str:
    if not name:
        return ""
    target = _stem_key(name)
    for path in sorted(root.glob("src/**/*.py"))[:2000]:
        if _stem_key(path.stem) == target or path.stem.startswith(name):
            return path.relative_to(root).as_posix()
    return ""


def _choose_verb(tokens: set[str]) -> str:
    best = ("route", 0)
    for verb, words in VERBS.items():
        hits = len(tokens & words)
        if hits > best[1]:
            best = (verb, hits)
    return best[0]
