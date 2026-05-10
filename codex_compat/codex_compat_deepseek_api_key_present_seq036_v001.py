"""codex_compat_deepseek_api_key_present_seq036_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

def _deepseek_api_key_present(root: Path) -> bool:
    if os.environ.get("DEEPSEEK_API_KEY"):
        return True
    env_path = Path(root) / ".env"
    if not env_path.exists():
        return False
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("DEEPSEEK_API_KEY=") and line.split("=", 1)[1].strip():
                return True
    except Exception:
        return False
    return False
