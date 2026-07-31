"""opus_prompt_box_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import CANDIDATES_LOG
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _append_jsonl
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _now
from pathlib import Path
from typing import Any
import json
import re

def queue_prompt_box_candidate(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Non-writer surfaces call this instead of touching task_queue directly."""
    root = Path(root)
    if record.get("void"):
        return {"status": "skipped", "reason": "void"}
    candidate = {
        "ts": record.get("ts") or _now(),
        "source": record.get("source") or "intent_key_generator",
        "intent_key": record.get("intent_key", ""),
        "scope": record.get("scope", ""),
        "prompt": str(record.get("prompt") or "")[:300],
        "confidence": float(record.get("confidence") or 0.0),
        "manifest_path": record.get("manifest_path", ""),
        "intent_id": record.get("intent_id", ""),
        "kind": record.get("kind") or "intent_key",
    }
    path = root / CANDIDATES_LOG
    _append_jsonl(path, candidate)
    return {"status": "candidate", "path": str(path), "intent_key": candidate["intent_key"]}
