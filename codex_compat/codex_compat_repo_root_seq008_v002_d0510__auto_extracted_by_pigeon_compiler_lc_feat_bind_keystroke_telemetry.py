"""codex_compat_repo_root_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 9 lines | ~78 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    if here.name == "codex_compat" and (here.parent / "codex_compat.py").exists():
        return here.parent
    return here
