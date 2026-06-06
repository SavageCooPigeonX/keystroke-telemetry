"""file_self_sim_learning_seq001_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from typing import Any
import re

def _drop_stale_runtime_sources(intent: str, sources: dict[str, Any]) -> None:
    latest_intent = (sources.get("latest") or {}).get("intent") or {}
    latest_raw = str(latest_intent.get("raw") or (sources.get("intent_latest") or {}).get("prompt") or "")
    if not latest_raw:
        return
    current = set(_tokens(intent))
    previous = set(_tokens(latest_raw))
    if not current or not previous:
        return
    overlap = len(current & previous) / max(1, min(len(current), len(previous)))
    if overlap >= 0.35:
        return
    sources["latest"] = {"stale_runtime_source": latest_intent.get("intent_key", "")}
    sources["council"] = {}
    counts = sources.get("source_counts") or {}
    counts["proposals"] = 0
    counts["council_jobs"] = 0
    counts["stale_runtime_sources_dropped"] = 1
    sources["source_counts"] = counts
