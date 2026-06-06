"""batch_rewrite_sim_seq001_seq031_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from .batch_rewrite_sim_seq001_seq033_v001 import _stem_key
from .batch_rewrite_sim_seq001_seq033_v001 import _tokens
from .batch_rewrite_sim_seq001_seq034_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import re
import subprocess

def _interlink_score(rel: str, validation: dict[str, Any], compiled: dict[str, Any]) -> float:
    score = 0.0
    if _source_candidate(rel):
        score += 0.25
    refs = validation.get("referenced_by") or []
    imports = validation.get("imports") or []
    score += min(len(refs), 8) * 0.045
    score += min(len(imports), 10) * 0.02
    tokens = set(compiled.get("tokens") or [])
    path_tokens = _tokens(rel)
    score += min(len(tokens & path_tokens), 6) * 0.055
    if validation.get("line_count", 0) > 400:
        score -= 0.08
    return max(0.0, min(1.0, score))


def _load_failure_model(root: Path) -> dict[str, Any]:
    data = _load_json(root / "logs" / "self_fix_accuracy.json")
    if not isinstance(data, dict):
        data = {}
    persistent = []
    for row in data.get("persistent_top_10", []) or []:
        mod = str(row.get("module") or "").strip()
        if mod:
            persistent.append(_stem_key(mod))
    return {"avg_fix_rate": data.get("avg_fix_rate"), "persistent_modules": persistent}


def _git_status(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    dirty = set()
    for line in result.stdout.splitlines():
        if len(line) >= 4:
            dirty.add(line[3:].replace("\\", "/"))
    return dirty
