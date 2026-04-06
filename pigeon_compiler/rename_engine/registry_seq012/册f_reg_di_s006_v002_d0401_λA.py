"""registry_seq012_diff_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import re

def diff_registry_vs_disk(root: Path, entries: dict) -> dict:
    """Compare registry against actual files on disk.

    Returns {missing_on_disk: [...], new_on_disk: [...], moved: [...]}
    """
    from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project

    catalog = scan_project(root)
    disk_paths = {f['path'] for f in catalog['files'] if not f['is_init']}
    reg_paths = set(entries.keys())

    return {
        'missing_on_disk': sorted(reg_paths - disk_paths),
        'new_on_disk': sorted(disk_paths - reg_paths),
        'matched': sorted(reg_paths & disk_paths),
    }
