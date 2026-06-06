"""file_self_sim_learning_seq001_seq019_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq020_v001 import _update_file_profiles
from .file_self_sim_learning_seq001_seq022_v001 import _render_learning_markdown
from .file_self_sim_learning_seq001_seq040_v001 import _write_json
from .file_self_sim_learning_seq001_seq041_v001 import _append_jsonl
from pathlib import Path
from typing import Any
import json
import re

def _write_learning_outputs(root: Path, result: dict[str, Any], settings: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _write_json(logs / "file_self_sim_learning_latest.json", result)
    _write_json(logs / "file_relationship_graph.json", result.get("relationship_graph") or {})
    _write_json(logs / "file_identity_registry.json", result.get("architecture_sequence_registry") or {})
    _write_json(logs / "overcap_split_jobs.json", result.get("overcap_split_jobs") or [])
    _append_jsonl(logs / "file_self_sim_learning.jsonl", result)
    (logs / "file_self_sim_learning.md").write_text(_render_learning_markdown(result), encoding="utf-8")
    for packet in result.get("learning_packets") or []:
        _append_jsonl(logs / "deepseek_learning_packets.jsonl", packet)
    try:
        from src.file_sim_deepseek_lane_seq001_v001 import queue_perpendicular_deepseek_job
        result["perpendicular_deepseek"] = queue_perpendicular_deepseek_job(root, result, write=True)
        _write_json(logs / "file_self_sim_learning_latest.json", result)
    except Exception as exc:
        result["perpendicular_deepseek_error"] = str(exc)
        _write_json(logs / "file_self_sim_learning_latest.json", result)
    if settings.get("update_file_profiles", True):
        _update_file_profiles(root, result)
    try:
        from src.file_email_plugin_seq001_v001 import emit_learning_digest_email
        result["learning_digest_email"] = emit_learning_digest_email(root, result)
        _write_json(logs / "file_self_sim_learning_latest.json", result)
    except Exception as exc:
        result["learning_digest_email_error"] = str(exc)
        _write_json(logs / "file_self_sim_learning_latest.json", result)
