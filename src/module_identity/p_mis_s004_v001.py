"""module_identity_seq001_v001_sources_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 24 lines | ~251 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .p_miu_s002_v001 import _load_json

def _load_all_sources(root: Path) -> dict:
    """Load every data source once, return as lookup dict."""
    try:
        from src.numeric_surface_seq001_v001 import generate_surface
        generate_surface(root)
    except Exception:
        pass

    return {
        'registry': _load_json(root / 'pigeon_registry.json'),
        'heat_map': _load_json(root / 'file_heat_map.json'),
        'entropy_map': _load_json(root / 'logs' / 'entropy_map.json'),
        'numeric_surface_seq001_v001': _load_json(root / 'logs' / 'numeric_surface_seq001_v001.json'),
        'bug_profiles_seq001_v001': _load_json(root / 'logs' / 'bug_profiles_seq001_v001.json'),
        'file_profiles': _load_json(root / 'file_profiles.json'),
        'death_log': _load_json(root / 'execution_death_log.json'),
        'dossier': _load_json(root / 'logs' / 'active_dossier.json'),
        'loop_detector': _load_json(root / 'loop_detector.json'),
    }
