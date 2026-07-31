"""organization_pass_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .organization_pass_seq001_v001_compiled_seq007_v001 import FileInfo
from .organization_pass_seq001_v001_compiled_seq007_v001 import MAX_PY_LINES
from .organization_pass_seq001_v001_compiled_seq007_v001 import ROOT_SRC_FAMILIES
from pathlib import Path
from typing import Any
import re

def _move_plan(root: Path, infos: list[FileInfo]) -> list[dict[str, Any]]:
    rows = []
    for info in infos:
        if not info.rel.startswith("src/") or "/" in info.rel.removeprefix("src/"):
            continue
        stem = Path(info.rel).stem
        target = _target_folder(stem)
        if not target or target == "src":
            continue
        if info.line_count <= MAX_PY_LINES and stem.startswith("__"):
            continue
        rows.append({
            "file": info.rel,
            "target_folder": target,
            "target_path": f"{target}/{Path(info.rel).name}",
            "reason": _move_reason(info, target),
            "line_count": info.line_count,
            "imports": list(info.imports)[:12],
            "validation_gate": [
                f"py -m py_compile {info.rel}",
                "git grep old import path",
                f"refresh {target}/MANIFEST.md",
            ],
            "apply_now": False,
        })
    return sorted(rows, key=lambda row: (-row["line_count"], row["target_folder"], row["file"]))[:120]


def _target_folder(stem: str) -> str:
    base = re.sub(r"_(?:seq|s)?\d{3,}.*$", "", stem)
    key = base.split("_", 1)[0].lower()
    return ROOT_SRC_FAMILIES.get(key, "")


def _move_reason(info: FileInfo, target: str) -> str:
    pressure = "overcap" if info.line_count > MAX_PY_LINES else "root-src-bucket"
    return f"{pressure}; family should compile inside {target} instead of source warehouse"


def _mode(score: float, external: int, overcap: list[str], manifest_exists: bool) -> str:
    if not manifest_exists or len(overcap) >= 3:
        return "needs_manifest_room"
    if score >= 0.66 and external <= 2:
        return "self_managed"
    if score >= 0.45:
        return "local_with_explicit_external_edges"
    return "compiler_reorganization_needed"
