"""batch_rewrite_sim_seq001_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq034_v001 import DEFAULT_CONFIG
from .batch_rewrite_sim_seq001_seq034_v001 import _load_json
from .batch_rewrite_sim_seq001_seq034_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import os
import re

def load_file_sim_config(root: Path, write_default: bool = True) -> dict[str, Any]:
    root = Path(root)
    path = root / "logs" / "file_sim_config.json"
    raw = _load_json(path) if path.exists() else {}
    config = merge_file_sim_config(raw if isinstance(raw, dict) else {})
    if write_default and (not path.exists() or raw != config):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, config)
    return config


def merge_file_sim_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in (config or {}).items():
        if key in {"compiler_layers", "rewrite_orchestration", "consensus_guard", "orchestrator_policy"} and isinstance(value, dict):
            base = merged.get(key) if isinstance(merged.get(key), dict) else {}
            base.update(value)
            merged[key] = base
        elif key == "fire_on" and isinstance(value, list):
            merged[key] = list(dict.fromkeys([*DEFAULT_CONFIG["fire_on"], *value, "composition_submit", "os_hook_auto"]))
        else:
            merged[key] = value
    return merged


def should_fire_file_sim(config: dict[str, Any], trigger: str, prompt: str) -> bool:
    config = merge_file_sim_config(config)
    if not config.get("enabled", True):
        return False
    if trigger not in set(config.get("fire_on") or []):
        return False
    return len(str(prompt or "").strip()) >= int(config.get("min_chars") or 0)
