"""u_pd_s024_v001_colorize_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 12 lines | ~113 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _colorize(line: str, use_color: bool) -> str:
    if not use_color:
        return line
    if line.startswith('+') and not line.startswith('+++'):
        return _GREEN + line + _RESET
    if line.startswith('-') and not line.startswith('---'):
        return _RED + line + _RESET
    if line.startswith('@@'):
        return _CYAN + line + _RESET
    return line
