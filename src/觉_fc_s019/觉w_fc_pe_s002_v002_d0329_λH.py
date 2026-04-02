"""file_consciousness_seq019_persistence_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 18 lines | ~149 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
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
