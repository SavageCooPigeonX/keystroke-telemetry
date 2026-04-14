"""引w_ir_s003_v005_d0403_踪稿析_λFX_replace_exact_module_path_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 9 lines | ~101 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _replace_exact_module_path(line: str, old_mod: str, new_mod: str) -> str:
    """Rewrite only exact module-path tokens inside import statements."""
    pattern = re.compile(
        rf'(?<![\w.]){re.escape(old_mod)}(?=(?:\.|\s|,|$))'
    )
    return pattern.sub(new_mod, line)
