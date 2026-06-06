"""file_self_sim_learning_seq001_seq021_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from .file_self_sim_learning_seq001_seq040_v001 import _load_json
from .file_self_sim_learning_seq001_seq040_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def _apply_outcome_to_profiles(root: Path, record: dict[str, Any]) -> None:
    profiles = _load_json(root / "file_profiles.json") or {}
    touched = [record.get("file"), *[
        item.get("file") for item in record.get("backward_targets", [])
        if isinstance(item, dict)
    ]]
    for rel in _dedupe(touched):
        if not rel:
            continue
        key = _stem_key(rel)
        profile = profiles.setdefault(key, {})
        outcomes = profile.setdefault("learning_outcomes", [])
        outcomes.append({
            "ts": record.get("ts"),
            "packet_id": record.get("packet_id"),
            "outcome": record.get("outcome"),
            "reward": record.get("reward"),
            "intent_key": record.get("intent_key"),
        })
        profile["learning_outcomes"] = outcomes[-30:]
    _write_json(root / "file_profiles.json", profiles)
