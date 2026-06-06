"""file_self_sim_learning_seq001_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq024_v001 import _size_pressure
from .file_self_sim_learning_seq001_seq025_v001 import _parse_sequence_markers
from .file_self_sim_learning_seq001_seq025_v001 import _scope_for_file
from .file_self_sim_learning_seq001_seq036_v001 import _candidate_allowed
from .file_self_sim_learning_seq001_seq036_v001 import _scan_repo_files
from .file_self_sim_learning_seq001_seq039_v001 import _estimate_tokens
from .file_self_sim_learning_seq001_seq039_v001 import _line_count
from .file_self_sim_learning_seq001_seq040_v001 import _load_json
from .file_self_sim_learning_seq001_seq041_v001 import _now
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _architecture_sequence_registry(root: Path, settings: dict[str, Any]) -> dict[str, Any]:
    existing = _load_json(root / "logs" / "file_identity_registry.json") or {}
    previous: dict[str, str] = {
        str(item.get("file")): str(item.get("arch_seq"))
        for item in existing.get("files", []) or []
        if item.get("file") and item.get("arch_seq")
    }
    max_arch = 0
    for value in previous.values():
        match = re.search(r"(\d+)$", value)
        if match:
            max_arch = max(max_arch, int(match.group(1)))

    files = []
    next_arch = max_arch + 1
    for rel in sorted(_scan_repo_files(root)):
        if not _candidate_allowed(root, rel):
            continue
        line_count = _line_count(root, rel)
        local_seq, version = _parse_sequence_markers(rel)
        arch_seq = previous.get(rel)
        if not arch_seq:
            arch_seq = f"A-{next_arch:06d}"
            next_arch += 1
        pressure = _size_pressure(root, rel, settings)
        files.append({
            "file": rel,
            "file_id": "F-" + hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12],
            "arch_seq": arch_seq,
            "local_seq": local_seq,
            "version": version,
            "scope": _scope_for_file(rel),
            "line_count": line_count,
            "approx_tokens": _estimate_tokens(root, rel),
            "size_state": pressure.get("state"),
            "split_pressure": pressure.get("pressure", 0),
            "sequence_note": "global arch_seq is registry-owned; filename seq remains local to scope/module",
        })

    summary = Counter(item["size_state"] for item in files)
    return {
        "schema": "file_identity_registry/v1",
        "ts": _now(),
        "sequence_policy": {
            "filename_seq": "local_to_file_family_or_scope",
            "arch_seq": "global_registry_sequence_do_not_rename_files",
            "file_id": "stable_hash_of_relative_path",
        },
        "summary": {
            "files": len(files),
            "ok": summary.get("ok", 0),
            "over_soft": summary.get("over_soft", 0),
            "warn": summary.get("warn", 0),
            "critical": summary.get("critical", 0),
        },
        "files": files,
    }
