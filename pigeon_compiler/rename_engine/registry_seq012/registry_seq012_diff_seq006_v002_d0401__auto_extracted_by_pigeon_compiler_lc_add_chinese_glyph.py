"""registry_seq012_diff_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 20 lines | ~194 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: add_chinese_glyph
# LAST:   2026-04-01 @ aa32a3f
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

def diff_registry_vs_disk(root: Path, entries: dict) -> dict:
    """Compare registry against actual files on disk.

    Returns {missing_on_disk: [...], new_on_disk: [...], moved: [...]}
    """
    from pigeon_compiler.rename_engine.scanner_seq001_v004_d0315__扫_walk_the_project_tree_and_lc_verify_pigeon_plugin import scan_project

    catalog = scan_project(root)
    disk_paths = {f['path'] for f in catalog['files'] if not f['is_init']}
    reg_paths = set(entries.keys())

    return {
        'missing_on_disk': sorted(reg_paths - disk_paths),
        'new_on_disk': sorted(disk_paths - reg_paths),
        'matched': sorted(reg_paths & disk_paths),
    }
