"""copilot_prompt_manager_seq020_block_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

import re

def _block_pattern(start: str, end: str) -> re.Pattern[str]:
    return re.compile(
        rf'(?ms)^\s*{re.escape(start)}\s*$\n.*?^\s*{re.escape(end)}\s*$',
    )


def _extract_block(text: str, start: str, end: str) -> str | None:
    match = _block_pattern(start, end).search(text)
    return match.group(0) if match else None


def _replace_or_insert_after_line(text: str, anchor: str, block: str) -> str:
    anchor_pattern = re.compile(rf'(?m)^\s*{re.escape(anchor)}\s*$')
    match = anchor_pattern.search(text)
    if not match:
        return text.rstrip() + '\n\n' + block + '\n'
    insert_at = match.end()
    return text[:insert_at] + '\n\n' + block + text[insert_at:]


def _upsert_block(text: str, start: str, end: str, block: str, anchor: str | None = None) -> str:
    pattern = _block_pattern(start, end)
    if pattern.search(text):
        return pattern.sub(block, text)
    if anchor and anchor in text:
        return _replace_or_insert_after_line(text, anchor, block)
    return text.rstrip() + '\n\n' + block + '\n'
