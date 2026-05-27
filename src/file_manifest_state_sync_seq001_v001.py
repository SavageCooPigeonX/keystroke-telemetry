"""Sync file-sim collaboration state into folder MANIFEST.md files."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.file_manifest_state_render_seq001_v001 import (
    FOLDER_END,
    FOLDER_START,
    GLOBAL_END,
    GLOBAL_START,
    render_folder_block,
    render_global_block,
)


def sync_file_sim_manifest_state(
    root: Path,
    audit: dict[str, Any],
    *,
    write: bool = True,
) -> dict[str, Any]:
    """Write latest file-sim state into folder manifests plus root stage."""
    root = Path(root)
    comments = _comments(audit)
    by_folder = _comments_by_folder(comments)
    written = []
    for folder, rows in sorted(by_folder.items()):
        manifest = root / folder / "MANIFEST.md" if folder else root / "MANIFEST.md"
        if not manifest.exists():
            continue
        old = manifest.read_text(encoding="utf-8", errors="replace")
        new = _replace_block(old, FOLDER_START, FOLDER_END, render_folder_block(folder, rows, audit))
        changed = old != new
        if changed and write:
            manifest.write_text(new, encoding="utf-8")
        written.append({"manifest": _rel(root, manifest), "folder": folder or ".", "changed": changed, "comments": len(rows)})

    global_manifest = _global_manifest(root)
    global_changed = False
    if global_manifest.exists():
        old = global_manifest.read_text(encoding="utf-8", errors="replace")
        new = _replace_block(old, GLOBAL_START, GLOBAL_END, render_global_block(written, audit))
        global_changed = old != new
        if global_changed and write:
            global_manifest.write_text(new, encoding="utf-8")

    result = {
        "schema": "file_manifest_state_sync/v1",
        "ts": _now(),
        "mode": "write" if write else "dry_run",
        "global_manifest": _rel(root, global_manifest) if global_manifest.exists() else "",
        "global_changed": global_changed,
        "folder_manifests": written,
        "changed_count": sum(1 for row in written if row["changed"]) + int(global_changed),
        "state_rule": "folder MANIFEST.md is file-local collaboration state; root MANIFEST.md is global stage",
    }
    if write:
        _write_json(root / "logs" / "file_manifest_state_sync_latest.json", result)
        _append_jsonl(root / "logs" / "file_manifest_state_sync.jsonl", result)
    return result


def _replace_block(text: str, start: str, end: str, block: str) -> str:
    pattern = rf"\n?{re.escape(start)}.*?{re.escape(end)}\n?"
    clean = re.sub(pattern, "\n", text, flags=re.S).rstrip()
    return clean + "\n\n" + block.rstrip() + "\n"


def _comments(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rooms = (audit.get("manifest_state") or {}).get("rooms") or []
    rows: list[dict[str, Any]] = []
    for room in rooms:
        rows.extend(row for row in room.get("comments", []) if isinstance(row, dict))
    return rows


def _comments_by_folder(comments: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in comments:
        parent = Path(str(row.get("from_file") or "")).parent.as_posix()
        out["" if parent == "." else parent].append(row)
    return out


def _global_manifest(root: Path) -> Path:
    master = root / "MASTER_MANIFEST.md"
    return master if master.exists() else root / "MANIFEST.md"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")
