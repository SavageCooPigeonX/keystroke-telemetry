"""git_plugin_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

def _load_coaching_prose(root: Path) -> str | None:
    """Load LLM-generated coaching prose from operator_coaching.md if present."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return None
    try:
        text = coaching_path.read_text(encoding='utf-8')
        m = re.search(r'<!-- coaching:count=\d+ -->\n.*?\n(.*?)<!-- /coaching -->', text, re.DOTALL)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None
