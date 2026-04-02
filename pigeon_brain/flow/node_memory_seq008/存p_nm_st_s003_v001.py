"""node_memory_seq008_storage_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json

def load_memory(root: Path) -> dict[str, Any]:
    """Load the full node memory store."""
    p = _memory_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_memory(root: Path, memory: dict[str, Any]) -> None:
    """Persist node memory to disk."""
    p = _memory_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(memory, indent=2, default=str), encoding="utf-8")
