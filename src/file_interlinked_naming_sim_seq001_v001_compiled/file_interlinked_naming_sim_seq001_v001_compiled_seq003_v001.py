"""file_interlinked_naming_sim_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import _json
from pathlib import Path
import json
import re

def _select_files(root: Path, limit: int) -> list[str]:
    blank = _json(root / "logs" / "file_blank_sheet_sim_latest.json")
    files = [row.get("file", "") for row in blank.get("file_pressure_jobs") or []]
    symbolic = _first_symbolic_file(root)
    if symbolic and symbolic not in files[:limit]:
        files = [symbolic] + [file for file in files if file != symbolic]
    if len(files) < limit:
        files.extend(path.relative_to(root).as_posix() for path in sorted((root / "src").rglob("*.py"))[: limit * 3])
    out = []
    for file in files:
        if file and file not in out and (root / file).exists():
            out.append(file)
        if len(out) >= limit:
            break
    return out


def _first_symbolic_file(root: Path) -> str:
    for path in sorted((root / "src").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if any(ord(ch) > 127 for ch in rel):
            return rel
    return ""
