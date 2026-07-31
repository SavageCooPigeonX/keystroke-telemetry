"""unified_manifest_state_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json
import re

def _belongs(file_path: str, folder: str) -> bool:
    clean = file_path.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))

def _cell(value: Any, limit: int = 160) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]

def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None

FOLDER_START = "<!-- manifest:folder-unified-state -->"

FOLDER_END = "<!-- /manifest:folder-unified-state -->"

MASTER_START = "<!-- manifest:master-persistent-state -->"

MASTER_END = "<!-- /manifest:master-persistent-state -->"
