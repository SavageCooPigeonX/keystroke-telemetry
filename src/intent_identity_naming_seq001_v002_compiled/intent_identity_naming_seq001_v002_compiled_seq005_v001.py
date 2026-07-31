"""intent_identity_naming_seq001_v002_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .intent_identity_naming_seq001_v002_compiled_seq001_v001 import identity_id_from_path
from .intent_identity_naming_seq001_v002_compiled_seq003_v001 import parse_intent_stem
from .intent_identity_naming_seq001_v002_compiled_seq004_v001 import enrich_registry_entry
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _append_jsonl
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _now
from pathlib import Path
from typing import Any
import json
import re

def stamp_intent_touch(
    root: Path,
    file: str,
    *,
    intent_key: str,
    last_change: str,
    reason: str = "intent_touch",
    write: bool = True,
) -> dict[str, Any]:
    """Record ITID/LH/ECI + last_change for a touched file in registry."""
    root = Path(root)
    rel = str(file).replace("\\", "/").strip()
    from pigeon_compiler.rename_engine import load_registry, save_registry

    registry = load_registry(root)
    entry = dict(registry.get(rel) or {})
    if not entry:
        from pigeon_compiler.rename_engine import parse_pigeon_stem

        parsed = parse_pigeon_stem(Path(rel).stem) or parse_intent_stem(Path(rel).stem) or {}
        entry = {
            "path": rel,
            "name": parsed.get("name") or identity_id_from_path(rel),
            "seq": int(parsed.get("seq") or 0),
            "ver": int(parsed.get("ver") or 1),
            "date": parsed.get("date") or "",
            "desc": parsed.get("desc") or "",
            "intent": parsed.get("intent") or "",
            "history": [],
        }
    enrich_registry_entry(
        entry,
        path=rel,
        intent_key=intent_key,
        last_change=last_change or reason,
        event=reason,
    )
    entry["path"] = rel
    registry[rel] = entry
    result = {
        "schema": "intent_identity_touch/v1",
        "ts": _now(),
        "file": rel,
        "identity_id": entry.get("identity_id"),
        "itid": entry.get("itid"),
        "lh": entry.get("lh"),
        "eci": entry.get("eci"),
        "intent_key": entry.get("intent_key"),
        "last_change": entry.get("last_change"),
        "parent_lineage": entry.get("parent_lineage") or {},
    }
    if write:
        save_registry(root, registry)
        _append_jsonl(root / "logs/intent_identity_touches.jsonl", result)
    return result
