"""虚f_mc_s036_v001_profile_read_source_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 14 lines | ~135 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def read_source(root: Path, rel_path: str, max_lines: int = 120) -> str:
    p = root / rel_path
    if not p.exists():
        return ''
    try:
        lines = p.read_text('utf-8', errors='ignore').splitlines()
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f'\n# ... ({len(lines) - max_lines} more lines)'
        return '\n'.join(lines)
    except Exception:
        return ''
