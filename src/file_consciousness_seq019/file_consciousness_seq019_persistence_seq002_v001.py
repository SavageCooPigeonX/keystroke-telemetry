"""file_consciousness_seq019_persistence_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def save_profiles(root: Path, profiles: dict) -> Path:
    """Write dating profiles to file_profiles.json."""
    out = root / 'file_profiles.json'
    out.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding='utf-8')
    return out


def load_profiles(root: Path) -> dict:
    """Load cached dating profiles."""
    p = root / 'file_profiles.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text('utf-8'))
