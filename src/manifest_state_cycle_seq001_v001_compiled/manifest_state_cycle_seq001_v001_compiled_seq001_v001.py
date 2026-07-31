"""manifest_state_cycle_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .manifest_state_cycle_seq001_v001_compiled_seq002_v001 import _selected_files
from .manifest_state_cycle_seq001_v001_compiled_seq002_v001 import render_manifest_state_write
from .manifest_state_cycle_seq001_v001_compiled_seq003_v001 import _build_packet
from .manifest_state_cycle_seq001_v001_compiled_seq004_v001 import _selected_manifests
from .manifest_state_cycle_seq001_v001_compiled_seq004_v001 import _write_folder_manifests
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import HISTORY
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import LATEST
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import MARKDOWN
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _append_jsonl
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _now
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _write_json
from pathlib import Path
from src.folder_context_coupling_seq001_v001 import build_folder_context_coupling
from src.operator_syntax_triggers_seq001_v001 import learn_operator_syntax_triggers, match_operator_syntax_triggers
from src.unified_manifest_state_seq001_v001 import append_folder_unified_state, refresh_master_manifest
from typing import Any
import json

def apply_manifest_state_cycle(
    root: Path,
    prompt: str,
    *,
    focus_files: list[str] | None = None,
    use_prompt_packet: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Let selected files write bounded learned state into their folder manifests."""
    root = Path(root)
    packet = _build_packet(root, prompt, focus_files or [], use_prompt_packet, write)
    graph = packet.get("intent_key_encoding") or {}
    learn_operator_syntax_triggers(root, graph, write=write)
    syntax_files = match_operator_syntax_triggers(root, prompt, intent_key=" ".join(packet.get("manifest_state_protocol", {}).get("master_intent_keys", [])), limit=8)
    selected_files = _selected_files(packet, syntax_files)
    selected_manifests = _selected_manifests(packet)
    folder_coupling = build_folder_context_coupling(
        root,
        prompt,
        focus_files=selected_files,
        selected_manifests=selected_manifests,
        write=write,
    )
    file_writes = _write_folder_manifests(root, selected_files, write)
    master = refresh_master_manifest(root, selected_files, dry_run=not write)
    result = {
        "schema": "manifest_state_write_cycle/v1",
        "ts": _now(),
        "prompt_hash": packet.get("prompt_hash", ""),
        "status": "manifest_state_written" if write else "dry_run",
        "selected_files": selected_files,
        "selected_manifests": selected_manifests,
        "file_writes": file_writes,
        "master_manifest": master,
        "syntax_matched_files": syntax_files,
        "folder_context_coupling": folder_coupling,
        "manifest_syntax_match": (packet.get("manifest_state_protocol") or {}).get("manifest_syntax_match") or {},
        "rule": "files write only to their own folder MANIFEST.md; selected external manifests are read-only sim context",
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_manifest_state_write(result), encoding="utf-8")
    return result
