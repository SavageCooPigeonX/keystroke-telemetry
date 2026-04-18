"""管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_block_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 23 lines | ~225 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _block_pattern(start: str, end: str) -> re.Pattern[str]:
    return re.compile(rf'(?ms)^\s*{re.escape(start)}\s*$\n.*?^\s*{re.escape(end)}\s*$')


def _extract_block(text: str, start: str, end: str) -> str | None:
    match = _block_pattern(start, end).search(text)
    return match.group(0) if match else None


def _count_blocks(text: str, start: str, end: str) -> int:
    return len(_block_pattern(start, end).findall(text))


def _replace_or_insert_after_line(text: str, anchor: str, block: str) -> str:
    anchor_pattern = re.compile(rf'(?m)^\s*{re.escape(anchor)}\s*$')
    match = anchor_pattern.search(text)
    if not match:
        return text.rstrip() + '\n\n' + block + '\n'
    insert_at = match.end()
    return text[:insert_at] + '\n\n' + block + text[insert_at:]
