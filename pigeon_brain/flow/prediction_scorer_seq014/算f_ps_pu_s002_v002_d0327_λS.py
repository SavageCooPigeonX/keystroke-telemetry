"""prediction_scorer_seq014_path_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import re

def _scores_path(root: Path) -> Path:
    return root / "pigeon_brain" / SCORED_CACHE_FILE


def _calibration_path(root: Path) -> Path:
    return root / "pigeon_brain" / CALIBRATION_FILE
