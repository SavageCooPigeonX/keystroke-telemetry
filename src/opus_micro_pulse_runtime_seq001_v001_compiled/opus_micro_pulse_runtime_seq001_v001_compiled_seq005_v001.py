"""opus_micro_pulse_runtime_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from src.manifest_syntax_matcher_seq001_v001 import match_manifest_syntax
from typing import Any
import json
import re

def _explicit_runtime_files(text: str) -> list[str]:
    low = text.lower()
    rows = []
    if "manifest" in low:
        rows.extend(["MANIFEST.md", "ROOT_SIM_KEYS.md", "src/unified_manifest_state_seq001_v001.py"])
    if "root" in low or "sim key" in low:
        rows.extend(["src/root_sim_key_file_seq001_v001.py", "ROOT_SIM_KEYS.md"])
    if "prompt" in low:
        rows.extend(["src/prompt_manifest_compiler_seq001_v001.py", "logs/prompt_journal.jsonl"])
    if "file" in low and ("talk" in low or "comment" in low or "conscious" in low):
        rows.extend(["src/file_bug_chat_seq001_v001.py", "logs/file_bug_chat_latest.json"])
    if "backward" in low or "diff" in low:
        rows.extend(["src/codex_edit_outcome_binder_seq001_v001.py", "logs/edit_pairs.jsonl"])
    return rows


def _selected_manifests(root: Path, fragment: str, files: list[str]) -> list[dict[str, Any]]:
    try:
        match = match_manifest_syntax(root, fragment + " " + " ".join(files), limit=6, write=False)
        return match.get("selected_manifests") or []
    except Exception:
        return []
