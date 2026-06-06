"""batch_rewrite_sim_seq001_seq026_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from .batch_rewrite_sim_seq001_seq032_v001 import _resolve_stem
from .batch_rewrite_sim_seq001_seq033_v001 import _tokens
from .batch_rewrite_sim_seq001_seq034_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import os
import re

def _seed_paths(
    root: Path,
    compiled: dict[str, Any],
    dead_summary: dict[str, Any],
    context_selection: dict[str, Any] | None,
) -> list[tuple[str, float, str]]:
    seeds: list[tuple[str, float, str]] = []
    tokens = set(compiled.get("tokens") or [])
    manifest = str(compiled.get("manifest_path") or "")
    if manifest:
        seeds.append((manifest, 0.3, "latest_intent_manifest_context"))
        scope_dir = root / Path(manifest).parent
        if scope_dir.exists():
            for path in sorted(scope_dir.glob("*.py"))[:10]:
                seeds.append((path.relative_to(root).as_posix(), 0.9, "manifest_scope_file"))
    ctx = context_selection if isinstance(context_selection, dict) else (_load_json(root / "logs" / "context_selection.json") or {})
    for item in ctx.get("files", [])[:8]:
        raw_name = str(item.get("name", ""))
        resolved = _resolve_stem(root, raw_name)
        if resolved:
            seeds.append((resolved, 1.6, "numeric_context_selection"))
        elif raw_name:
            seeds.append((raw_name, 2.6, "numeric_context_selection_alias"))
    for item in (dead_summary.get("top_churn_files") or [])[:8]:
        churn_path = str(item.get("path", ""))
        seeds.append((churn_path, 0.35 if _source_candidate(churn_path) else 0.08, "top_churn_memory"))
    for path in sorted(root.glob("src/**/*.py"))[:2500]:
        rel = path.relative_to(root).as_posix()
        hits = len(tokens & _tokens(rel))
        if hits:
            seeds.append((rel, min(1.2, 0.2 + hits * 0.18), "intent_token_file_match"))
    return seeds


def _add_candidate(bucket: dict[str, dict[str, Any]], path: str, points: float, reason: str) -> None:
    if not path:
        return
    row = bucket[path.replace("\\", "/")]
    row["score"] += points
    if reason not in row["evidence"]:
        row["evidence"].append(reason)
