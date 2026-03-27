"""prediction_scorer_seq014_module_extractor_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v002 | 13 lines | ~112 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

def extract_module_name(filepath: str) -> str | None:
    """Extract pigeon module name from a file path."""
    if not filepath.endswith(".py"):
        return None
    stem = Path(filepath).stem
    m = re.match(r"^\.?([a-zA-Z_][a-zA-Z0-9_]*)_seq\d+", stem)
    if m:
        return m.group(1)
    return stem
