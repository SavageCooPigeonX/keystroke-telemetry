"""codex_compat_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json
import os
import re
import sys

def _write_text_resilient(path: Path, text: str) -> None:
    """Write text in a way that tolerates OneDrive/Windows target-file quirks."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        if tmp.exists():
            tmp.unlink()
        with path.open("r+", encoding="utf-8", errors="ignore", newline="") as handle:
            handle.seek(0)
            handle.write(text)
            handle.truncate()


def _load_jsonl_tail(path: Path, max_lines: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    if here.name == "codex_compat" and (here.parent / "codex_compat.py").exists():
        return here.parent
    return here


def _ensure_repo_on_path(root: Path) -> None:
    root_s = str(Path(root).resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
