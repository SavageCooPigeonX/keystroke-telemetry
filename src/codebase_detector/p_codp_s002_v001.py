"""codebase_detector_seq001_v001_profile_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 13 lines | ~103 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class CodebaseProfile:
    root: Path = field(default_factory=Path)
    name: str = ''
    kind: str = 'generic'
    modules: int = 0
    structured_files: dict = field(default_factory=dict)
    naming_pattern: str = 'standard'
    state_text: str = ''
