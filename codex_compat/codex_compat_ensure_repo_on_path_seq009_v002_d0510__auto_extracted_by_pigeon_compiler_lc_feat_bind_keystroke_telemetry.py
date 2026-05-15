"""codex_compat_ensure_repo_on_path_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v002 | 9 lines | ~72 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re
import sys

def _ensure_repo_on_path(root: Path) -> None:
    root_s = str(Path(root).resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
