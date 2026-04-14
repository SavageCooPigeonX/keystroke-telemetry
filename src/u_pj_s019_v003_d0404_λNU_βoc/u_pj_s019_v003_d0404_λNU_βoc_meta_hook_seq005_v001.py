"""u_pj_s019_v003_d0404_λNU_βoc_meta_hook_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 12 lines | ~106 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _is_meta_hook_message(msg: str) -> bool:
    low = msg.lower()
    return all(marker in low for marker in TASK_COMPLETE_HOOK_MARKERS)


def _is_operator_entry(entry: dict) -> bool:
    if entry.get('prompt_kind') == 'meta_hook':
        return False
    return not _is_meta_hook_message(str(entry.get('msg', '')))
