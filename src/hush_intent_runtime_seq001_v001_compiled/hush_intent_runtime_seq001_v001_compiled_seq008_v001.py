"""hush_intent_runtime_seq001_v001_compiled_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _tokens
from pathlib import Path
from typing import Any
import re

def _blocked_actions(fence: str) -> list[str]:
    blocked = ["autonomous_overwrite", "cross_repo_mutation"]
    if fence == "blocked":
        blocked.append("source_mutation")
    return blocked


def _responsibility(file: str, packet: dict[str, Any]) -> str:
    profile = packet.get("responsibility_profile") if isinstance(packet.get("responsibility_profile"), dict) else {}
    declared = str(profile.get("declared_role") or "")
    if declared:
        return declared
    stem = Path(file).stem
    words = _tokens(stem.replace("_", " "))
    return " ".join(words[:8]) or "file substrate participant"


def _neighbors(wake: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    out = []
    out.extend(str(x) for x in wake.get("known_neighbors") or [] if x)
    for item in wake.get("context_veins") or []:
        if isinstance(item, dict) and item.get("file"):
            out.append(str(item["file"]))
    out.extend(str(x) for x in packet.get("known_neighbors") or [] if x)
    return list(dict.fromkeys(out))[:8]


def _validation_gate(wake: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    tests = list(wake.get("tests") or packet.get("tests") or [])
    if tests:
        return [f"py -m pytest {tests[0]} -q"]
    file = str(wake.get("file") or packet.get("file") or "")
    return [f"py -m py_compile {file}"] if file.endswith(".py") else ["operator approval required"]


def _file_kind(file: str) -> str:
    name = Path(file).name
    if name.startswith("test_"):
        return "test"
    if any(ord(ch) > 127 for ch in name):
        return "symbolic_pigeon_name"
    if re.search(r"_seq\d+_v\d+", name):
        return "versioned_module"
    return "stable_facade"
