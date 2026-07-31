"""unified_manifest_state_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .unified_manifest_state_seq001_v001_compiled_seq002_v001 import render_folder_unified_state
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _extract_block
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _replace_block
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import FOLDER_END
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import FOLDER_START
from pathlib import Path
import re

def append_folder_unified_state(root: Path, content: str, folder: str, changed: list[str], old: str = "") -> str:
    content = _replace_block(content, FOLDER_START, FOLDER_END, "")
    existing = _extract_block(old, FOLDER_START, FOLDER_END)
    block = render_folder_unified_state(root, folder, changed)
    if existing == block:
        block = existing
    return content.rstrip() + "\n\n" + block + "\n"
