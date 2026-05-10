"""codex_compat_build_focus_files_seq039_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_git_focus_files_seq034_v001 import _git_focus_files
from .codex_compat_load_json_seq059_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import re

def _build_focus_files(
    context_selection: dict[str, Any],
    state: dict[str, Any],
    root: Path | None = None,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    focus: list[dict[str, Any]] = []
    alias_rows: dict[str, Any] = {}
    if root is not None:
        alias_data = _load_json(Path(root) / "logs" / "file_identity_aliases.json") or {}
        if isinstance(alias_data, dict) and isinstance(alias_data.get("aliases"), dict):
            alias_rows = alias_data["aliases"]

    for item in context_selection.get("files") or []:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        record = alias_rows.get(name.replace("\\", "/")) or {}
        targets = [
            str(target).replace("\\", "/")
            for target in (record.get("current_files") or [])
            if root is not None and (Path(root) / str(target)).exists()
        ]
        if not targets and record.get("current_file") and root is not None:
            candidate = str(record.get("current_file")).replace("\\", "/")
            if (Path(root) / candidate).exists():
                targets = [candidate]
        for target in (targets[:3] if targets else [name]):
            if target in seen:
                continue
            seen.add(target)
            reason = "numeric_context_alias" if target != name else "numeric_context"
            row = {"name": target, "reason": reason, "score": item.get("score", 0)}
            if target != name:
                row["alias_from"] = name
            focus.append(row)

    for edit in state.get("recent_edits") or []:
        file_name = str(edit.get("file") or "").strip()
        if not file_name or file_name in seen:
            continue
        seen.add(file_name)
        focus.append({"name": file_name, "reason": "recent_edit", "why": edit.get("edit_why", "")})

    for file_name in _git_focus_files(state.get("git_status") or []):
        if root is not None and not (Path(root) / file_name).is_file():
            continue
        if file_name in seen:
            continue
        seen.add(file_name)
        focus.append({"name": file_name, "reason": "dirty_git"})

    entropy = state.get("entropy") or {}
    for item in entropy.get("top_entropy_modules") or []:
        name = str(item.get("module") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        focus.append({
            "name": name,
            "reason": "entropy_watch",
            "entropy": item.get("avg_entropy"),
            "samples": item.get("samples"),
        })

    return focus[:16]
