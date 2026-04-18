"""钩w_th_s011_v002_d0323_缩分话_λP_build_module_map_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 22 lines | ~185 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _build_module_map(root: Path) -> dict:
    """Map absolute file paths to pigeon module names."""
    registry_path = root / "pigeon_registry.json"
    if not registry_path.exists():
        return {}
    try:
        registry = json.loads(registry_path.read_text("utf-8"))
    except Exception:
        return {}

    mapping = {}
    for entry in registry.get("files", []):
        name = entry.get("name", "")
        rel_path = entry.get("path", "")
        if name and rel_path:
            abs_path = str((root / rel_path).resolve())
            mapping[abs_path] = name
    return mapping
