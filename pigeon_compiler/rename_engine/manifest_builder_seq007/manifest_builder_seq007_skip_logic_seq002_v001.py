"""manifest_builder_seq007_skip_logic_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _should_skip(py: Path, root: Path) -> bool:
    parts = py.relative_to(root).parts
    for p in parts:
        if p in SKIP_DIRS or p.startswith('.venv') or p.startswith('_llm_tests'):
            return True
    return False
