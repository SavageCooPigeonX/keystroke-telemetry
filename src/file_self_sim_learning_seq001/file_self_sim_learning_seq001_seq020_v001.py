"""file_self_sim_learning_seq001_seq020_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _profile_hint
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from .file_self_sim_learning_seq001_seq040_v001 import _load_json
from .file_self_sim_learning_seq001_seq040_v001 import _write_json
from .file_self_sim_learning_seq001_seq041_v001 import _now
from pathlib import Path
from typing import Any
import json
import re

def _update_file_profiles(root: Path, result: dict[str, Any]) -> None:
    profiles = _load_json(root / "file_profiles.json") or {}
    ts = result.get("ts") or _now()
    intent_key = (result.get("intent") or {}).get("intent_key", "")
    graph_nodes = {
        item.get("file"): item
        for item in (result.get("relationship_graph") or {}).get("nodes", [])
        if isinstance(item, dict)
    }
    split_jobs = {
        item.get("file"): item
        for item in result.get("overcap_split_jobs") or []
        if isinstance(item, dict)
    }
    registry = {
        item.get("file"): item
        for item in (result.get("architecture_sequence_registry") or {}).get("files", [])
        if isinstance(item, dict)
    }
    for packet in result.get("learning_packets") or []:
        rel = packet.get("file", "")
        key = _stem_key(rel)
        profile = profiles.setdefault(key, {})
        history = profile.setdefault("learning_history", [])
        history.append({
            "ts": ts,
            "packet_id": packet.get("packet_id"),
            "file": rel,
            "intent_key": intent_key,
            "mode": result.get("mode"),
            "wake_role": packet.get("wake_role"),
            "wake_score": (packet.get("intent_profile") or {}).get("wake_score", 0),
            "overwrite_readiness": packet.get("overwrite_readiness", {}),
        })
        profile["learning_history"] = history[-30:]
        profile["self_sim_profile"] = {
            "file": rel,
            "responsibility_profile": packet.get("responsibility_profile", {}),
            "context_veins": packet.get("context_veins", []),
            "relationship_weight": packet.get("relationship_weight", 0),
            "relationship_memory": graph_nodes.get(rel, {}),
            "size_pressure": packet.get("size_pressure", {}),
            "split_plan_request": packet.get("split_plan_request", {}),
            "architecture_identity": registry.get(rel, {}),
            "verification_packet": packet.get("verification_packet", {}),
            "last_packet_id": packet.get("packet_id"),
            "target_state": result.get("target_state"),
        }
        profile["self_repair_hint"] = _profile_hint(packet)
        profile["overwrite_readiness"] = packet.get("overwrite_readiness", {})
        profile["split_plan_job"] = split_jobs.get(rel, {})
        watch = profile.setdefault("backwards_pass_watch", [])
        for target in packet.get("backward_learning_targets") or []:
            file_name = target.get("file") if isinstance(target, dict) else str(target)
            if file_name and file_name not in watch:
                watch.insert(0, file_name)
        profile["backwards_pass_watch"] = watch[:12]
        profiles[key] = profile
    _write_json(root / "file_profiles.json", profiles)
