"""module_identity_sources_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _load_all_sources(root: Path) -> dict:
    """Load every data source once, return as lookup dict."""
    try:
        from src.numeric_surface import generate_surface
        generate_surface(root)
    except Exception:
        pass

    return {
        'registry': _load_json(root / 'pigeon_registry.json'),
        'heat_map': _load_json(root / 'file_heat_map.json'),
        'entropy_map': _load_json(root / 'logs' / 'entropy_map.json'),
        'numeric_surface': _load_json(root / 'logs' / 'numeric_surface.json'),
        'bug_profiles': _load_json(root / 'logs' / 'bug_profiles.json'),
        'file_profiles': _load_json(root / 'file_profiles.json'),
        'death_log': _load_json(root / 'execution_death_log.json'),
        'dossier': _load_json(root / 'logs' / 'active_dossier.json'),
        'loop_detector': _load_json(root / 'loop_detector.json'),
    }
