"""batch_rewrite_sim_seq001_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq032_v001 import _choose_verb
from .batch_rewrite_sim_seq001_seq033_v001 import _choose_scope_from_manifests
from .batch_rewrite_sim_seq001_seq033_v001 import _token_list
from .batch_rewrite_sim_seq001_seq034_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import os
import re

def compile_intent(root: Path, intent: str = "") -> dict[str, Any]:
    root = Path(root)
    latest = _load_json(Path(root) / "logs" / "intent_key_latest.json") or {}
    raw = (intent or latest.get("prompt") or "").strip()
    words = _token_list(raw)
    tokens = set(words)
    verb = _choose_verb(tokens)
    scale = "major" if tokens & {"rewrite", "rewrites", "batch", "migrate", "migration"} else "patch"
    if intent:
        scope_info = _choose_scope_from_manifests(root, tokens)
        scope = scope_info.get("scope", "root")
        manifest_path = scope_info.get("manifest_path", "")
        confidence = scope_info.get("confidence", 0)
    else:
        scope = str(latest.get("scope") or "root")
        manifest_path = str(latest.get("manifest_path", ""))
        confidence = latest.get("confidence", 0)
    target = "_".join(words[:5])[:64] or str(latest.get("target") or "work")
    return {
        "raw": raw,
        "tokens": words[:40],
        "intent_key": f"{scope}:{verb}:{target}:{scale}",
        "scope": scope,
        "verb": verb,
        "target": target,
        "scale": scale,
        "manifest_path": manifest_path,
        "latest_confidence": confidence,
    }
