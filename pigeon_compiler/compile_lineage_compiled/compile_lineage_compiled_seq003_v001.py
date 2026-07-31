"""compile_lineage_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .compile_lineage_compiled_seq005_v001 import ALIAS_SCHEMA
from .compile_lineage_compiled_seq005_v001 import _load_json
from .compile_lineage_compiled_seq005_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def _merge_aliases(path: Path, lineage: dict[str, Any]) -> None:
    data = _load_json(path)
    if not isinstance(data, dict) or data.get("schema") != ALIAS_SCHEMA:
        data = {"schema": ALIAS_SCHEMA, "aliases": {}, "sources": {}}
    aliases = data.setdefault("aliases", {})
    sources = data.setdefault("sources", {})
    source_file = lineage.get("source_file", "")
    generated_files = []
    for entry in lineage.get("files") or []:
        generated = entry.get("generated_file", "")
        if generated:
            generated_files.append(generated)
        for alias in entry.get("aliases") or []:
            aliases[alias] = {
                "current_file": generated,
                "current_files": [generated] if generated else [],
                "source_file": source_file,
                "source_symbols": entry.get("source_symbols", []),
                "identity_key": entry.get("identity_key", ""),
                "compiled_at": lineage.get("compiled_at", ""),
            }
    if source_file:
        aliases[source_file] = {
            "current_file": generated_files[0] if generated_files else "",
            "current_files": generated_files,
            "source_file": source_file,
            "source_symbols": [],
            "identity_key": f"{source_file}::*",
            "compiled_at": lineage.get("compiled_at", ""),
        }
        sources[source_file] = {
            "target_dir": lineage.get("target_dir", ""),
            "compiled_at": lineage.get("compiled_at", ""),
            "current_files": generated_files,
        }
    _write_json(path, data)


def _cut_symbols(cut: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    for key in ("functions", "classes", "constants", "contents", "new_helpers"):
        for value in cut.get(key) or []:
            text = str(value).strip()
            if text and text not in symbols:
                symbols.append(text)
    return symbols
