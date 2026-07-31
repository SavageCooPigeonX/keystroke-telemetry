"""folder_context_coupling_seq001_v001_compiled_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import PACKAGE_RANK_SCAN_CAP
from pathlib import Path
from typing import Any
import json

def _package_folders(root: Path, selected_folders: list[str]) -> list[str]:
    folders = list(dict.fromkeys(selected_folders))
    for selected in selected_folders:
        base = root if selected == "." else root / selected
        if not base.exists():
            continue
        for manifest in base.rglob("MANIFEST.md"):
            rel = manifest.parent.relative_to(root).as_posix()
            folder = "." if rel == "." else rel
            if selected == "." and "/" in folder:
                continue
            folders.append(folder)
            if len(folders) >= PACKAGE_RANK_SCAN_CAP:
                break
    return list(dict.fromkeys(folders))


def _rank_packages(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: (
            row.get("recommended_mode") != "self_managed",
            row.get("scan_cap_hit", False),
            row.get("overcap_file_count", 0),
            row.get("resistance_score", 1),
            -row.get("autonomy_score", 0),
            row.get("external_edge_count", 0),
            row.get("folder", ""),
        ),
    )
    ranked = []
    for idx, row in enumerate(ordered[:30], start=1):
        ranked.append({"rank": idx, **row})
    return ranked


def _folder_of(rel: str) -> str:
    parent = Path(rel.strip("\"'")).parent.as_posix()
    return "." if parent in {"", "."} else parent


def _belongs(rel: str, folder: str) -> bool:
    clean = rel.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
