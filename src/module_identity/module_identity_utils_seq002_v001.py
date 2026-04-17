"""module_identity_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 26 lines | ~196 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .module_identity_constants_seq001_v001 import MEMORY_DIR

def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return {}


def _load_memory(root: Path, name: str) -> dict:
    """Load persistent memory for a module."""
    mem_path = root / MEMORY_DIR / f'{name}.json'
    return _load_json(mem_path)


def _save_memory(root: Path, name: str, memory: dict):
    """Persist module memory."""
    mem_dir = root / MEMORY_DIR
    mem_dir.mkdir(parents=True, exist_ok=True)
    mem_path = mem_dir / f'{name}.json'
    mem_path.write_text(json.dumps(memory, indent=2, ensure_ascii=False), 'utf-8')
