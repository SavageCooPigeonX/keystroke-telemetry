"""codex_compat_write_text_resilient_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

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
