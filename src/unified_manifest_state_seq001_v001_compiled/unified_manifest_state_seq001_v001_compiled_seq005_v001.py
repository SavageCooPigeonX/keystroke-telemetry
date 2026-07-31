"""unified_manifest_state_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import _belongs
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import re

def _folder_rows(root: Path, changed: list[str]) -> list[dict[str, Any]]:
    manifests = sorted(path for path in root.rglob("MANIFEST.md") if ".git" not in path.parts)
    rows = []
    for manifest in manifests:
        folder = manifest.parent.relative_to(root).as_posix() if manifest.parent != root else "."
        count = sum(1 for rel in changed if _belongs(rel, folder))
        rows.append({"folder": folder, "manifest": manifest.relative_to(root).as_posix(), "changed_count": count})
    return rows

def _syntax_rows(root: Path, folder: str) -> list[dict[str, Any]]:
    state = _load_json(root / "logs" / "operator_syntax_triggers.json") or {}
    rows = [row for row in (state.get("files") or {}).values() if _belongs(str(row.get("file") or ""), folder)]
    rows.sort(key=lambda row: int(row.get("observations") or 0), reverse=True)
    return rows

def _state_files() -> list[str]:
    return [
        "logs/prompt_context_packet_latest.json",
        "logs/copilot_prompt_box_latest.md",
        "logs/intent_graph_latest.json",
        "logs/operator_syntax_triggers.json",
        "logs/opus_master_manifest_session.json",
        "logs/deepseek_push_audit_latest.json",
        "logs/file_bug_surface_latest.json",
        "logs/file_bug_chat_latest.json",
        "logs/root_sim_key_file_latest.json",
        "logs/opus_micro_pulse_latest.json",
        "logs/opus_executor_prompt_latest.md",
        "logs/prompt_cannon_job_latest.json",
        "logs/cannon_execution_gate_latest.json",
        "logs/backward_file_intelligence_learning_pending_latest.json",
    ]

def _latest_protocol(root: Path) -> dict[str, Any]:
    packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    return packet.get("manifest_state_protocol") or {}

def _bug_rows(root: Path) -> list[dict[str, Any]]:
    surface = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    return surface.get("bugs") or []

def _bug_chat_rows(root: Path) -> list[dict[str, Any]]:
    chat = _load_json(root / "logs" / "file_bug_chat_latest.json") or {}
    return chat.get("comments") or []

def _replace_block(text: str, start: str, end: str, replacement: str) -> str:
    return re.sub(rf"\n?{re.escape(start)}.*?{re.escape(end)}\n?", replacement, text, flags=re.S).rstrip()

def _extract_block(text: str, start: str, end: str) -> str:
    match = re.search(rf"{re.escape(start)}.*?{re.escape(end)}", text, flags=re.S)
    return match.group(0).strip() if match else ""
