"""opus_micro_pulse_runtime_seq001_v001_compiled_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import re

def _stale_flags(root: Path, files: list[str]) -> list[dict[str, Any]]:
    surface = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    bugs = surface.get("bugs") or []
    rows = []
    owners = set(files)
    for bug in bugs:
        title = str(bug.get("title") or "").lower()
        owner = str(bug.get("owner") or "")
        if owner in owners or "stale" in title:
            rows.append({
                "owner": owner,
                "severity": bug.get("severity"),
                "title": bug.get("title"),
                "next_action": bug.get("next_action"),
            })
        if len(rows) >= 8:
            break
    return rows


def _theories(pulse: dict[str, Any]) -> list[dict[str, Any]]:
    files = pulse.get("selected_files") or []
    stale = pulse.get("stale_flags") or []
    cls = pulse.get("prompt_class")
    return [
        {
            "theory": "intent_route",
            "confidence": round(min(0.95, 0.35 + len(files) * 0.06), 3),
            "reason": f"{len(files)} files self-selected for {cls} policy",
        },
        {
            "theory": "stale_poison_risk",
            "confidence": round(min(0.9, 0.2 + len(stale) * 0.09), 3),
            "reason": f"{len(stale)} stale flags must be shown before executor action",
        },
        {
            "theory": "missed_file_learning",
            "confidence": 0.72 if files else 0.31,
            "reason": "Codex diff will train files touched-but-not-predicted after execution",
        },
    ]
