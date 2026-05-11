"""codex_compat_git_focus_files_seq034_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 034 | VER: v002 | 13 lines | ~111 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _git_focus_files(git_status: list[str]) -> list[str]:
    files: list[str] = []
    for line in git_status:
        parts = line.strip().split(maxsplit=1)
        if not parts:
            continue
        candidate = parts[-1].strip()
        if candidate and candidate not in files:
            files.append(candidate)
    return files[:12]
