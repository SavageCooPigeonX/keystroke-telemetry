"""codex_compat_ensure_repo_on_path_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re
import sys

def _ensure_repo_on_path(root: Path) -> None:
    root_s = str(Path(root).resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
