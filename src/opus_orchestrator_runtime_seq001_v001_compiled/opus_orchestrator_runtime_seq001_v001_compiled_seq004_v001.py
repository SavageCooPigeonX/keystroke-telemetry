"""opus_orchestrator_runtime_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _json
from pathlib import Path
from typing import Any
import json

def _macro_cycle_summary(macro: dict[str, Any]) -> dict[str, Any]:
    cycles = macro.get("cycles") or []
    return {
        "path": "logs/session_macro_cycle_latest.json",
        "status": "needs_audit" if any(row.get("status") != "complete_enough" for row in cycles) else "complete_enough",
        "macro_read": macro.get("macro_read", ""),
        "known_agent_sessions": macro.get("known_agent_sessions") or [],
        "latest_prompt_deleted_words": macro.get("latest_prompt_deleted_words") or [],
        "cycles": [
            {
                "cycle_id": row.get("cycle_id", ""),
                "status": row.get("status", ""),
                "prompt_count": row.get("prompt_count", 0),
                "intent_keys": row.get("intent_keys", [])[:5],
            }
            for row in cycles[:3]
        ],
    }


def _manifest_write_cycle_summary(root: Path) -> dict[str, Any]:
    latest = _json(root / "logs" / "manifest_state_write_latest.json")
    return {
        "path": "logs/manifest_state_write_latest.json",
        "status": latest.get("status", "missing"),
        "file_writes": (latest.get("file_writes") or [])[:8],
        "selected_manifests": (latest.get("selected_manifests") or [])[:8],
        "manifest_syntax_match": ((latest.get("manifest_syntax_match") or {}).get("selected_manifests") or [])[:5],
    }


def _folder_context_coupling_summary(root: Path) -> dict[str, Any]:
    latest = _json(root / "logs" / "folder_context_coupling_latest.json")
    folders = latest.get("folders") or []
    return {
        "path": "logs/folder_context_coupling_latest.json",
        "status": "missing" if not latest else "needs_manifest_manager" if any(row.get("recommended_mode") != "self_managed" for row in folders) else "self_managed",
        "folders": folders[:8],
        "cross_folder_edges": (latest.get("cross_folder_edges") or [])[:8],
        "deepseek_manifest_manager": latest.get("deepseek_manifest_manager") or {},
    }


def _coding_memory_summary(memory: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": "logs/opus_coding_area_memory_latest.json",
        "job_count": len(memory.get("file_jobs") or []),
        "top_files": [row.get("file", "") for row in (memory.get("blocks") or [])[:6]],
        "contract": memory.get("orchestration_contract") or {},
    }
