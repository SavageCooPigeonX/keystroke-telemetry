"""管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_upsert_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 10 lines | ~117 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _upsert_block(text: str, start: str, end: str, block: str, anchor: str | None = None) -> str:
    pattern = _block_pattern(start, end)
    if pattern.search(text):
        return pattern.sub(block, text)
    if anchor and anchor in text:
        return _replace_or_insert_after_line(text, anchor, block)
    return text.rstrip() + '\n\n' + block + '\n'
