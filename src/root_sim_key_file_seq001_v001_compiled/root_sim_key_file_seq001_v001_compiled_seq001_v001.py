"""root_sim_key_file_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .root_sim_key_file_seq001_v001_compiled_seq002_v001 import render_root_sim_key_file
from .root_sim_key_file_seq001_v001_compiled_seq003_v001 import _attention_plan
from .root_sim_key_file_seq001_v001_compiled_seq004_v001 import _add_probe_cycle
from .root_sim_key_file_seq001_v001_compiled_seq004_v001 import _add_prompt_packet
from .root_sim_key_file_seq001_v001_compiled_seq004_v001 import _write_live_manifest_receipts
from .root_sim_key_file_seq001_v001_compiled_seq005_v001 import _add_bug_chat
from .root_sim_key_file_seq001_v001_compiled_seq005_v001 import _add_opus_pulse
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import DEFAULT_ATTENTION_LIMIT
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import ROOT_KEY
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import _append_jsonl
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import _load_json
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import _now
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import _write_json
from pathlib import Path
from typing import Any
import json

def build_root_sim_key_file(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    probe = _load_json(root / "logs" / "copilot_probe_push_cycle_latest.json") or {}
    chat = _load_json(root / "logs" / "file_bug_chat_latest.json") or {}
    pulse = _load_json(root / "logs" / "opus_micro_pulse_latest.json") or {}
    rows: dict[str, dict[str, Any]] = {}
    _add_prompt_packet(rows, packet)
    _add_probe_cycle(rows, probe)
    _add_bug_chat(rows, chat)
    _add_opus_pulse(rows, pulse)
    ordered = sorted(rows.values(), key=lambda row: (row.get("kind", ""), row.get("file", "")))
    attention = _attention_plan(ordered, DEFAULT_ATTENTION_LIMIT)
    result = {
        "schema": "root_sim_key_file/v1",
        "ts": _now(),
        "path": ROOT_KEY,
        "called_count": len(ordered),
        "attention_limit": DEFAULT_ATTENTION_LIMIT,
        "attention_selected_count": len(attention),
        "attention_plan": attention,
        "called_files": ordered,
        "source_paths": [
            "logs/prompt_context_packet_latest.json",
            "logs/copilot_probe_push_cycle_latest.json",
            "logs/file_bug_chat_latest.json",
            "logs/opus_micro_pulse_latest.json",
        ],
    }
    if write:
        _write_json(root / "logs" / "root_sim_key_file_latest.json", result)
        _append_jsonl(root / "logs" / "root_sim_key_file.jsonl", result)
        (root / ROOT_KEY).write_text(render_root_sim_key_file(result), encoding="utf-8")
        _write_live_manifest_receipts(root, result)
    return result
