"""unified_manifest_state_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .unified_manifest_state_seq001_v001_compiled_seq004_v001 import append_master_persistent_state
from pathlib import Path
from typing import Any
import re

def refresh_master_manifest(root: Path, changed: list[str], *, dry_run: bool = False) -> dict[str, Any]:
    root = Path(root)
    path = root / "MANIFEST.md"
    old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else "# MASTER MANIFEST\n"
    new = append_master_persistent_state(root, old, changed)
    changed_flag = old != new
    if changed_flag and not dry_run:
        path.write_text(new, encoding="utf-8")
    return {"path": "MANIFEST.md", "changed": changed_flag}
