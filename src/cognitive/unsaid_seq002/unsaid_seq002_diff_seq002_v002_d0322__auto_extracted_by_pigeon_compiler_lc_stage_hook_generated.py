"""unsaid_seq002_diff_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 19 lines | ~178 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_hook_generated
# LAST:   2026-03-22 @ b48ee0a
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _diff_deleted(before: str, after: str) -> str:
    """Find text that was in 'before' but removed in 'after'."""
    if after in before:
        idx = before.find(after)
        deleted_before = before[:idx]
        deleted_after = before[idx + len(after):]
        return (deleted_before + deleted_after).strip()
    if len(before) <= len(after):
        return ''
    common_start = 0
    for i in range(min(len(before), len(after))):
        if before[i] == after[i]:
            common_start = i + 1
        else:
            break
    return before[common_start:len(before) - max(0, len(after) - common_start)].strip()
