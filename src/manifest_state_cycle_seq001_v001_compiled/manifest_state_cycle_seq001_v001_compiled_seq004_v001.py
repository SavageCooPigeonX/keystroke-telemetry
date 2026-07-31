"""manifest_state_cycle_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _belongs
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _own_manifest
from pathlib import Path
from src.unified_manifest_state_seq001_v001 import append_folder_unified_state, refresh_master_manifest
from typing import Any

def _selected_manifests(packet: dict[str, Any]) -> list[dict[str, Any]]:
    protocol = packet.get("manifest_state_protocol") or {}
    rows = [{"manifest": row.get("manifest"), "source": "manifest_read_set"} for row in protocol.get("read_set", [])]
    rows.extend({
        "manifest": row.get("manifest"),
        "source": "manifest_syntax_match",
        "score": row.get("score"),
        "matched_tokens": row.get("matched_tokens") or [],
    } for row in (protocol.get("manifest_syntax_match") or {}).get("selected_manifests", []))
    out = []
    seen = set()
    for row in rows:
        key = row.get("manifest")
        if key and key not in seen:
            seen.add(key)
            out.append(row)
    return out


def _write_folder_manifests(root: Path, files: list[str], write: bool) -> list[dict[str, Any]]:
    rows = []
    for rel in files:
        manifest = _own_manifest(root, rel)
        if not manifest or not manifest.exists():
            continue
        folder = "." if manifest.parent == root else manifest.parent.relative_to(root).as_posix()
        old = manifest.read_text(encoding="utf-8", errors="replace")
        scoped = [file for file in files if _belongs(file, folder)]
        new = append_folder_unified_state(root, old, folder, scoped, old)
        changed = old != new
        if changed and write:
            manifest.write_text(new, encoding="utf-8")
        rows.append({
            "file": rel,
            "manifest": manifest.relative_to(root).as_posix(),
            "folder": folder,
            "changed": changed,
            "reason": "syntax_or_context_selected_file_state",
        })
    return rows
