"""codebase_detector_seq001_v001_orchestrator_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 23 lines | ~238 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def detect_codebase(root: Path) -> CodebaseProfile:
    """Scan root for structured metadata — returns compact profile."""
    profile = CodebaseProfile(root=root, name=root.name)
    for key, fname in _STRUCTURE_FILES.items():
        p = root / fname
        if p.exists():
            profile.structured_files[key] = p
    if 'pigeon_registry' in profile.structured_files:
        profile.kind = 'pigeon'
        profile.naming_pattern = 'semantic_glyph'
    elif 'cargo' in profile.structured_files:
        profile.kind = 'rust'
    elif 'package_json' in profile.structured_files:
        profile.kind = 'node'
    elif 'pyproject' in profile.structured_files:
        profile.kind = 'python'
    profile.modules = _count_modules(root, profile.kind)
    profile.state_text = _build_state_text(profile)
    return profile
