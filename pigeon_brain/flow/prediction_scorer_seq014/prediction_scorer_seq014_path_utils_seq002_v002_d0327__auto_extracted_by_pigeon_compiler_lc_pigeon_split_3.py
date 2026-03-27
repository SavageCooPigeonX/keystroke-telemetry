"""prediction_scorer_seq014_path_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 10 lines | ~79 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _scores_path(root: Path) -> Path:
    return root / "pigeon_brain" / SCORED_CACHE_FILE


def _calibration_path(root: Path) -> Path:
    return root / "pigeon_brain" / CALIBRATION_FILE
