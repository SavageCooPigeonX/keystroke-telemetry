"""copilot_prompt_manager_seq020_json_utils_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _registry_items(registry: dict | None) -> list[tuple[str, dict]]:
    if not registry:
        return []
    if isinstance(registry, dict) and isinstance(registry.get('files'), list):
        items: list[tuple[str, dict]] = []
        for entry in registry['files']:
            if isinstance(entry, dict):
                items.append((entry.get('path', ''), entry))
        return items
    if isinstance(registry, dict):
        items = []
        for path, entry in registry.items():
            if isinstance(entry, dict):
                items.append((path, entry))
        return items
    return []
