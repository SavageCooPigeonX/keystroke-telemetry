"""codex_compat_git_changed_files_seq067_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re
import subprocess

def _git_changed_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
