"""opus_micro_pulse_runtime_seq001_v001_compiled_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq015_v001 import _append_pulse_folder_block
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _folder_for
from pathlib import Path
from typing import Any
import re

def _write_manifest_state(root: Path, result: dict[str, Any]) -> None:
    try:
        from src.unified_manifest_state_seq001_v001 import refresh_master_manifest
    except Exception:
        return
    files = (result.get("cannon_job") or {}).get("predicted_files") or []
    for folder in sorted({_folder_for(rel) for rel in files}):
        manifest = root / ("MANIFEST.md" if folder in {"", "."} else f"{folder}/MANIFEST.md")
        if not manifest.exists():
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(f"# MANIFEST - {folder or '.'}\n", encoding="utf-8")
        old = manifest.read_text(encoding="utf-8", errors="ignore")
        new = _append_pulse_folder_block(old, folder, result)
        if new != old:
            manifest.write_text(new, encoding="utf-8")
    refresh_master_manifest(root, files, dry_run=False)
