"""file_email_plugin_seq001_seq035_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq036_v001 import _file_memory_message
from .file_email_plugin_seq001_seq036_v001 import _file_memory_thread_id
from .file_email_plugin_seq001_seq037_v001 import _empty_file_memory_knowledge
from .file_email_plugin_seq001_seq037_v001 import _merge_file_memory_knowledge
from .file_email_plugin_seq001_seq039_v001 import _render_file_memory
from .file_email_plugin_seq001_seq040_v001 import _write_file_memory_index
from .file_email_plugin_seq001_seq051_v001 import _load_json
from .file_email_plugin_seq001_seq051_v001 import _rel
from .file_email_plugin_seq001_seq051_v001 import _safe_filename
from .file_email_plugin_seq001_seq052_v001 import DEFAULT_CONFIG
from .file_email_plugin_seq001_seq052_v001 import _append_jsonl
from .file_email_plugin_seq001_seq052_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def _write_file_mail_memory(
    root: Path,
    config: dict[str, Any],
    record: dict[str, Any],
    body: str,
    paths: dict[str, str],
) -> dict[str, Any]:
    root = Path(root)
    file_path = str(record.get("file") or "unknown")
    mem_paths = _file_memory_paths(root, config, file_path)
    memory = _load_json(mem_paths["json_abs"])
    if not isinstance(memory, dict) or memory.get("schema") != "file_mail_memory/v1":
        memory = {
            "schema": "file_mail_memory/v1",
            "thread_id": _file_memory_thread_id(file_path),
            "file": file_path,
            "created_at": record.get("ts"),
            "messages": [],
            "knowledge": _empty_file_memory_knowledge(),
        }
    event = _file_memory_message(record, body, paths, direction="outbound")
    memory.setdefault("messages", []).append(event)
    memory["updated_at"] = record.get("ts")
    memory["knowledge"] = _merge_file_memory_knowledge(memory.get("knowledge"), event)
    mem_paths["json_abs"].parent.mkdir(parents=True, exist_ok=True)
    _write_json(mem_paths["json_abs"], memory)
    mem_paths["md_abs"].write_text(_render_file_memory(memory), encoding="utf-8")
    _write_json(root / "logs" / "file_memory_latest.json", memory)
    _append_jsonl(root / "logs" / "file_memory_messages.jsonl", event)
    _write_file_memory_index(root, config)
    return {
        "schema": "file_mail_memory_ref/v1",
        "thread_id": memory.get("thread_id"),
        "path": _rel(root, mem_paths["json_abs"]),
        "markdown": _rel(root, mem_paths["md_abs"]),
        "message_count": len(memory.get("messages") or []),
        "knowledge": memory.get("knowledge", {}),
        "mode": "email_thread_is_memory",
    }


def _file_memory_paths(root: Path, config: dict[str, Any], file_path: str) -> dict[str, Path]:
    memory_dir = root / str(config.get("memory_dir") or DEFAULT_CONFIG["memory_dir"])
    safe = _safe_filename(str(file_path).replace("\\", "__").replace("/", "__"))
    return {"json_abs": memory_dir / f"{safe}.json", "md_abs": memory_dir / f"{safe}.md"}
