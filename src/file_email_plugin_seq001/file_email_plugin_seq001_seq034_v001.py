"""file_email_plugin_seq001_seq034_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq035_v001 import _file_memory_paths
from .file_email_plugin_seq001_seq036_v001 import _file_memory_thread_id
from .file_email_plugin_seq001_seq037_v001 import _empty_file_memory_knowledge
from .file_email_plugin_seq001_seq051_v001 import _load_json
from .file_email_plugin_seq001_seq051_v001 import _rel
from pathlib import Path
from typing import Any
import json
import re

def _file_mail_memory_hint(root: Path, config: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    paths = _file_memory_paths(root, config, str(record.get("file") or "unknown"))
    existing = _load_json(paths["json_abs"]) or {}
    messages = existing.get("messages") if isinstance(existing.get("messages"), list) else []
    knowledge = existing.get("knowledge") if isinstance(existing.get("knowledge"), dict) else _empty_file_memory_knowledge()
    return {
        "schema": "file_mail_memory_ref/v1",
        "thread_id": _file_memory_thread_id(str(record.get("file") or "unknown")),
        "path": _rel(root, paths["json_abs"]),
        "markdown": _rel(root, paths["md_abs"]),
        "message_count": len(messages) + 1,
        "knowledge": knowledge,
        "mode": "email_thread_is_memory",
    }
