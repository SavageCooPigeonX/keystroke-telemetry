"""file_self_sim_learning_seq001_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq035_v001 import _prompt_numeric_encoding
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from .file_self_sim_learning_seq001_seq039_v001 import _fallback_intent_key
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
from typing import Any
import re

def _intent_model(root: Path, intent: str, sources: dict[str, Any]) -> dict[str, Any]:
    latest_intent = (sources.get("latest") or {}).get("intent") or {}
    intent_latest = sources.get("intent_latest") or {}
    raw = (
        intent
        or latest_intent.get("raw")
        or intent_latest.get("prompt")
        or intent_latest.get("raw")
        or ""
    ).strip()
    tokens = _tokens(raw)
    if intent and not sources.get("source_result_present"):
        intent_key = _fallback_intent_key(tokens)
    else:
        intent_key = (
            latest_intent.get("intent_key")
            or intent_latest.get("intent_key")
            or _fallback_intent_key(tokens)
        )
    explicit_intent = bool(intent and not sources.get("source_result_present"))
    unique_tokens = _dedupe(tokens)
    return {
        "raw": raw,
        "tokens": tokens[:80],
        "intent_key": intent_key,
        "scope": "root" if explicit_intent else latest_intent.get("scope") or intent_latest.get("scope") or "root",
        "target": "_".join(unique_tokens[:5]) if explicit_intent else latest_intent.get("target") or intent_latest.get("target") or "_".join(unique_tokens[:5]),
        "scale": ("major" if "rewrite" in tokens or "overwrite" in tokens else "patch") if explicit_intent else latest_intent.get("scale") or ("major" if "rewrite" in tokens else "patch"),
        "numeric_prompt_encoding": _prompt_numeric_encoding(root, raw, sources),
    }
