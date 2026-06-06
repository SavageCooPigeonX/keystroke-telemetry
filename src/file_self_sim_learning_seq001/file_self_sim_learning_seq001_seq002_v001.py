"""file_self_sim_learning_seq001_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq035_v001 import _load_numeric_surface
from .file_self_sim_learning_seq001_seq040_v001 import _load_json
from .file_self_sim_learning_seq001_seq041_v001 import DEFAULT_CONFIG
from .file_self_sim_learning_seq001_seq041_v001 import _load_jsonl
from pathlib import Path
from typing import Any
import json
import re

def _merge_config(config: dict[str, Any] | None) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in (config or {}).items():
        if key in merged:
            merged[key] = value
    merged["mode"] = "learning_only_no_overwrite"
    merged["overwrite_allowed"] = False
    return merged


def _load_signal_sources(root: Path, source_result: dict[str, Any] | None) -> dict[str, Any]:
    logs = root / "logs"
    latest = source_result or _load_json(logs / "batch_rewrite_sim_latest.json") or {}
    council = latest.get("file_job_council") or _load_json(logs / "file_job_council_latest.json") or {}
    memory_index = _load_json(logs / "file_memory_index.json") or {}
    file_profiles = _load_json(root / "file_profiles.json") or {}
    identity_growth = _load_jsonl(logs / "file_identity_growth.jsonl", 400)
    dead_pairs = _load_jsonl(logs / "dead_token_collective_pairs.jsonl", 400)
    learning_outcomes = _load_jsonl(logs / "file_self_sim_learning_outcomes.jsonl", 600)
    intent_latest = _load_json(logs / "intent_key_latest.json") or {}
    numeric = _load_numeric_surface(root)
    return {
        "source_result_present": source_result is not None,
        "latest": latest,
        "council": council,
        "memory_index": memory_index,
        "file_profiles": file_profiles,
        "identity_growth": identity_growth,
        "dead_pairs": dead_pairs,
        "learning_outcomes": learning_outcomes,
        "intent_latest": intent_latest,
        "numeric": numeric,
        "source_counts": {
            "proposals": len(latest.get("proposals") or []),
            "council_jobs": len(council.get("jobs") or []),
            "memory_files": len(memory_index.get("files") or []),
            "identity_growth": len(identity_growth),
            "history_pairs": len(dead_pairs),
            "learning_outcomes": len(learning_outcomes),
            "numeric_files": len((numeric.get("matrix") or {})),
        },
    }
