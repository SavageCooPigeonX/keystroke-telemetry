"""codex_compat_git_focus_files_seq034_v001.py — Auto-extracted by Pigeon Compiler."""
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
