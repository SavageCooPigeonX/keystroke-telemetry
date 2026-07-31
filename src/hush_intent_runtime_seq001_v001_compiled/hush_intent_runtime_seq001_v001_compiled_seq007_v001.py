"""hush_intent_runtime_seq001_v001_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq008_v001 import _blocked_actions
from .hush_intent_runtime_seq001_v001_compiled_seq008_v001 import _file_kind
from .hush_intent_runtime_seq001_v001_compiled_seq008_v001 import _neighbors
from .hush_intent_runtime_seq001_v001_compiled_seq008_v001 import _responsibility
from .hush_intent_runtime_seq001_v001_compiled_seq008_v001 import _validation_gate
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _json
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LOCAL_REPO
from pathlib import Path
from src.file_number_key_identity_seq001_v001 import file_identity_card
from typing import Any
import json
import re

def _local_file_packet(file: str, wake: dict[str, Any], source_packet: dict[str, Any], repo: dict[str, Any]) -> dict[str, Any]:
    identity = file_identity_card(file, _file_kind(file), str(wake.get("wake_reason") or "current prompt wake"))
    fence = repo.get("mutation_fence")
    return {
        "schema": "hush_file_packet/v1",
        "repo": LOCAL_REPO,
        "file": file,
        "file_identity": identity["number_key"],
        "operator_display_name": identity["operator_display_name"],
        "current_responsibility": _responsibility(file, source_packet),
        "last_change_state": identity["mutation_name"],
        "wake_reason": str(wake.get("wake_reason") or "selected by Hush runtime"),
        "allowed_actions": _allowed_actions(fence),
        "blocked_actions": _blocked_actions(fence),
        "neighbor_context": _neighbors(wake, source_packet),
        "validation_gate": _validation_gate(wake, source_packet),
        "memory_write_target": f"logs/file_memory/{file.replace('/', '__')}.json",
    }


def _repo_fingerprint_packets(root: Path, label: str, repo: dict[str, Any]) -> list[dict[str, Any]]:
    data = _json(root / "logs" / f"repo_fingerprint_{label}.json")
    rows = []
    for item in (data.get("files") or [])[:8]:
        identity = str(item.get("identity") or "")
        rows.append({
            "schema": "hush_file_packet/v1",
            "repo": label,
            "file": identity,
            "file_identity": identity,
            "operator_display_name": "Repo-Room-" + identity.replace("_", "-")[:80],
            "current_responsibility": "closed-repo context participant; source remains privacy fenced",
            "last_change_state": "fingerprint_indexed_not_source_mutated",
            "wake_reason": "active repo fingerprint matched operator intent",
            "allowed_actions": _allowed_actions(repo.get("mutation_fence")),
            "blocked_actions": ["source_mutation", "raw_source_exfiltration"],
            "neighbor_context": [],
            "validation_gate": ["repo lock", "operator opens exact file before mutation"],
            "memory_write_target": f"logs/file_memory/{identity}.json",
        })
    return rows


def _allowed_actions(fence: str) -> list[str]:
    if fence == "open":
        return ["read", "plan", "artifact", "validated_patch_after_approval"]
    return ["read", "plan", "artifact_only", "ask_for_repo_lock"]
