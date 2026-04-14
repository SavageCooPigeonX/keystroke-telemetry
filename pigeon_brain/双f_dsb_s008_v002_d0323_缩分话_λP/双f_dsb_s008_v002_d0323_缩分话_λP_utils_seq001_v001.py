"""双f_dsb_s008_v002_d0323_缩分话_λP_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 46 lines | ~332 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .描p_ghm_s004_v002_d0323_缩环检意_λP import HEAT_STORE
from pathlib import Path
import json

def _load_human_heat_raw(root: Path) -> dict:
    """Load raw file_heat_map.json (not the summary)."""
    heat_path = root / "file_heat_map.json"
    if not heat_path.exists():
        return {}
    try:
        return json.loads(heat_path.read_text("utf-8"))
    except Exception:
        return {}


def _load_agent_heat_raw(root: Path) -> dict:
    """Load raw graph_heat_map.json keyed by node name."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        return json.loads(heat_path.read_text("utf-8"))
    except Exception:
        return {}


def _load_file_profiles(root: Path) -> dict:
    """Load file_profiles.json for personality/fears/partners."""
    path = root / "file_profiles.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return {}


def _count_lines(root: Path, rel_path: str) -> int:
    """Count lines in a source file."""
    if not rel_path:
        return 0
    try:
        return len((root / rel_path).read_text("utf-8").splitlines())
    except Exception:
        return 0
