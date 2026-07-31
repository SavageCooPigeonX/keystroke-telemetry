"""hush_intent_runtime_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq007_v001 import _local_file_packet
from .hush_intent_runtime_seq001_v001_compiled_seq007_v001 import _repo_fingerprint_packets
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LOCAL_REPO
from pathlib import Path
from typing import Any
import re

def _files_for_move(name: str) -> list[str]:
    table = {
        "hush_intent_runtime": ["src/hush_intent_runtime_seq001_v001.py", "src/opus_orchestrator_runtime_seq001_v001.py"],
        "repo_classification": ["src/hush_intent_runtime_seq001_v001.py", "src/ai_fingerprint_repo_seq001_v001.py"],
        "linkrouter_file_room_access": ["src/ai_fingerprint_repo_seq001_v001.py", "docs/LINKROUTER_AI_MAP.md"],
        "file_mail_quality_gate": ["src/file_email_plugin_seq001_v001.py", "src/file_email_text_chain_seq001_v001.py"],
        "file_identity_narrative": ["src/file_number_key_identity_seq001_v001.py", "src/file_interlinked_naming_sim_seq001_v001.py"],
        "field_whisper_irt_future_layer": ["src/hush_intent_runtime_seq001_v001.py"],
    }
    return table.get(name, [])


def _file_packets(root: Path, repo: dict[str, Any], sim: dict[str, Any], prompt: str) -> list[dict[str, Any]]:
    if repo.get("active_repo") not in {LOCAL_REPO, "ambiguous"}:
        return _repo_fingerprint_packets(root, str(repo.get("active_repo")), repo)
    rows = []
    wake = sim.get("wake_order") if isinstance(sim.get("wake_order"), list) else []
    packets = sim.get("learning_packets") if isinstance(sim.get("learning_packets"), list) else []
    by_file = {str(p.get("file")): p for p in packets if isinstance(p, dict) and p.get("file")}
    for item in wake[:8]:
        file = str(item.get("file") or "")
        if not file:
            continue
        source_packet = by_file.get(file, {})
        rows.append(_local_file_packet(file, item, source_packet, repo))
    if not rows:
        for file in _files_for_move("hush_intent_runtime")[:3]:
            rows.append(_local_file_packet(file, {"wake_reason": "Hush runtime bootstrap"}, {}, repo))
    return rows
