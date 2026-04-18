"""引w_ir_s003_v005_d0403_踪稿析_λFX_rewrite_file_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 13 lines | ~131 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _rewrite_file(text: str, import_map: dict, stem_map: dict) -> tuple:
    changes = []
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        new_line = _rewrite_line(line, import_map, stem_map)
        if new_line != line:
            changes.append({'old_line': line.strip(), 'new_line': new_line.strip()})
        new_lines.append(new_line)
    return '\n'.join(new_lines), changes
