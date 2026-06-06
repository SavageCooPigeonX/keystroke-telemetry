"""file_self_sim_learning_seq001_seq025_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq024_v001 import _size_pressure
from .file_self_sim_learning_seq001_seq026_v001 import _reason_not_to_split
from .file_self_sim_learning_seq001_seq027_v001 import _proposed_split_children
from pathlib import Path
from typing import Any
import re

def _split_plan_request(
    root: Path,
    rel: str,
    node: dict[str, Any],
    validation_plan: list[str],
    settings: dict[str, Any],
) -> dict[str, Any]:
    size = node.get("size_pressure") or _size_pressure(root, rel, settings)
    if not size.get("needs_split_plan"):
        return {"needed": False, "reason": "file is within configured line cap"}
    tests = node.get("tests") or []
    return {
        "needed": True,
        "mode": "deepseek_split_plan_only",
        "approval_gate": "operator_required",
        "reason": "file is over cap; plan extraction before any source rewrite",
        "reason_not_to_split": _reason_not_to_split(rel, tests, node.get("known_neighbors") or []),
        "proposed_children": _proposed_split_children(root, rel),
        "validation_plan": validation_plan[:6],
    }


def _parse_sequence_markers(rel: str) -> tuple[str, str]:
    name = Path(rel).name
    seq = ""
    version = ""
    seq_match = re.search(r"(?:^|_)seq(\d{3})(?=_|\.|$)", name) or re.search(r"_s(\d{3})(?=_|\.|$)", name)
    version_match = re.search(r"_v(\d{3})(?=_|\.|$)", name)
    if seq_match:
        seq = f"seq{seq_match.group(1)}"
    if version_match:
        version = f"v{version_match.group(1)}"
    return seq, version


def _scope_for_file(rel: str) -> str:
    parts = Path(rel).parts
    if len(parts) <= 1:
        return "root"
    if parts[0] in {"src", "client", "tests", "pigeon_brain", "pigeon_compiler"}:
        return "/".join(parts[:2]) if len(parts) > 2 else parts[0]
    return parts[0]
