"""codex_compat_repo_root_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    if here.name == "codex_compat" and (here.parent / "codex_compat.py").exists():
        return here.parent
    return here
