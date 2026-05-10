"""codex_compat_git_status_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re
import subprocess

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
