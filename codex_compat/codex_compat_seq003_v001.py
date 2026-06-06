"""codex_compat_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _repo_root
from pathlib import Path
from typing import Any
import importlib.util
import re
import subprocess

def _load_entropy_module() -> Any | None:
    module_path = _repo_root() / "src" / "entropy_shedding_seq001_v001.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("codex_entropy_shedding", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_status(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--short"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]
