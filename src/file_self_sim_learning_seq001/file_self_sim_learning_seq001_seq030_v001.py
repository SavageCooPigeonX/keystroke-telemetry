"""file_self_sim_learning_seq001_seq030_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from .file_self_sim_learning_seq001_seq040_v001 import _load_json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import json
import re

def _memory_for_file(root: Path, rel: str, sources: dict[str, Any], allow_read: bool = True) -> dict[str, Any]:
    for item in (sources.get("memory_index") or {}).get("files") or []:
        if _clean_rel(item.get("file")) != rel:
            continue
        notes = []
        commands: dict[str, list[str]] = defaultdict(list)
        if allow_read:
            path = Path(item.get("path") or "")
            if not path.is_absolute():
                path = root / path
            data = _load_json(path) or {}
            for message in data.get("messages", [])[-12:]:
                for key, values in (message.get("commands") or {}).items():
                    for value in values or []:
                        commands[key].append(str(value))
                preview = str(message.get("body_preview") or "").strip()
                if preview and len(notes) < 4:
                    notes.append(preview[:180])
        command_summary = {
            key: _dedupe(values)[-5:]
            for key, values in commands.items()
        }
        summary_bits = []
        for key in ("remember", "use", "avoid", "style"):
            if command_summary.get(key):
                summary_bits.append(f"{key}: {command_summary[key][-1]}")
        return {
            "messages": int(item.get("messages") or 0),
            "thread": item.get("markdown") or item.get("path") or "",
            "commands": command_summary,
            "notes": notes,
            "summary": "; ".join(summary_bits) or f"{item.get('messages', 0)} stored message(s)",
        }
    return {"messages": 0, "thread": "", "commands": {}, "notes": [], "summary": "no durable memory yet"}


def _profile_for_file(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    profiles = sources.get("file_profiles") or {}
    return profiles.get(_stem_key(rel), {})


def _growth_for_file(rel: str, sources: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in (sources.get("identity_growth") or [])
        if _clean_rel(row.get("file")) == rel
    ][-12:]
