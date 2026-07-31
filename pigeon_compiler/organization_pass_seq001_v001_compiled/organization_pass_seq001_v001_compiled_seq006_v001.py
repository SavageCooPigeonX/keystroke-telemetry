"""organization_pass_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .organization_pass_seq001_v001_compiled_seq002_v001 import render_organization_plan
from .organization_pass_seq001_v001_compiled_seq007_v001 import FileInfo
from .organization_pass_seq001_v001_compiled_seq007_v001 import HISTORY
from .organization_pass_seq001_v001_compiled_seq007_v001 import LATEST
from .organization_pass_seq001_v001_compiled_seq007_v001 import MARKDOWN
from .organization_pass_seq001_v001_compiled_seq007_v001 import MAX_PY_LINES
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _summary(infos: list[FileInfo], folders: list[dict[str, Any]], moves: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "files_scanned": len(infos),
        "folders_scanned": len(folders),
        "candidate_moves": len(moves),
        "overcap_files": sum(1 for item in infos if item.line_count > MAX_PY_LINES),
        "parse_errors": sum(1 for item in infos if item.parse_error),
        "self_managed_folders": sum(1 for row in folders if row["recommended_mode"] == "self_managed"),
        "needs_manifest_room": sum(1 for row in folders if row["recommended_mode"] == "needs_manifest_room"),
    }


def _operator_label(folder: str) -> str:
    if folder == ".":
        return "Root Manifest-inator"
    leaf = folder.strip("/").split("/")[-1]
    words = re.findall(r"[A-Za-z0-9]+", leaf.replace("_", " "))
    if not words:
        words = ["Symbolic", "Room"]
    return " ".join(word.title() for word in words[:3]) + "-inator"


def _folder_of(rel: str) -> str:
    parent = Path(rel).parent.as_posix()
    return "." if parent in {"", "."} else parent


def _module_name(root: Path, path: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write_outputs(root: Path, plan: dict[str, Any]) -> None:
    _write_json(root / LATEST, plan)
    _append_jsonl(root / HISTORY, plan)
    (root / MARKDOWN).write_text(render_organization_plan(plan), encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
