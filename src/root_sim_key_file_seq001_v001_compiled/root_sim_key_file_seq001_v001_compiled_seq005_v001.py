"""root_sim_key_file_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import _local_manifest
from typing import Any

def _add_bug_chat(rows: dict[str, dict[str, Any]], chat: dict[str, Any]) -> None:
    for comment in chat.get("comments") or []:
        owner = str(comment.get("owner") or "")
        row = _merge(rows, owner, "bug_chat", comment.get("why_touched", ""), comment.get("intent_key", ""))
        row["operator_comment"] = comment.get("operator_comedy", "")
        row["coding_agent_note"] = comment.get("coding_agent_note", "")
        row["opus_note"] = comment.get("opus_manager_note", "")
        row["learned"] = comment.get("learned_from_sim", "")
        row["interlink_score"] = comment.get("interlink_score")

def _add_opus_pulse(rows: dict[str, dict[str, Any]], pulse: dict[str, Any]) -> None:
    for item in (pulse.get("cannon_job") or {}).get("predicted_files") or []:
        _merge(rows, str(item), "opus_pulse", "Opus pause pulse predicted this file before Enter", "")
    for pulse_row in pulse.get("pulses") or []:
        for item in pulse_row.get("file_interrogations") or []:
            rel = str(item.get("file") or "")
            row = _merge(rows, rel, "opus_pulse", item.get("opus_reason", ""), ",".join(item.get("intent_keys") or []))
            if item.get("file_comment"):
                row["operator_comment"] = item.get("file_comment", "")
            if item.get("coding_agent_note"):
                row["coding_agent_note"] = item.get("coding_agent_note", "")
            if item.get("deepseek_folder_manager_note"):
                row["opus_note"] = item.get("deepseek_folder_manager_note", "")
            row["learned"] = item.get("mismatch", "")

def _merge(rows: dict[str, dict[str, Any]], file_path: str, kind: str, why: Any, intent_key: str) -> dict[str, Any]:
    key = file_path.strip()
    row = rows.setdefault(key, {
        "file": key,
        "kind": kind,
        "local_manifest": _local_manifest(key),
        "why": "",
        "intent_keys": [],
        "operator_comment": "",
        "coding_agent_note": "",
        "opus_note": "",
        "learned": "",
    })
    kinds = set(str(row.get("kind") or "").split("+"))
    kinds.add(kind)
    row["kind"] = "+".join(sorted(k for k in kinds if k))
    if why and str(why) not in str(row.get("why") or ""):
        row["why"] = (str(row.get("why") or "") + " " + str(why)).strip()
    if intent_key:
        row["intent_keys"] = list(dict.fromkeys([*row.get("intent_keys", []), str(intent_key)]))
    return row
