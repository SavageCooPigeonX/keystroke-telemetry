"""u_pe_s024_v004_d0403_λP0_βoc_strip_blocks_seq003a_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _strip_query_blocks(text: str) -> tuple[str, bool]:
    """Remove all managed current-query blocks, even if duplicates exist."""
    lines = text.splitlines()
    kept = []
    in_block = False
    removed = False

    for line in lines:
        stripped = line.strip()
        if stripped == BLOCK_START:
            in_block = True
            removed = True
            continue
        if in_block:
            if stripped == BLOCK_END:
                in_block = False
            continue
        kept.append(line)

    cleaned = '\n'.join(kept).rstrip()
    legacy_pat = re.compile(
        r'(?ms)^## What You Actually Mean Right Now\s*\n.*?^\s*'
        + re.escape(BLOCK_END)
        + r'\s*$\n?'
    )
    cleaned, legacy_n = legacy_pat.subn('', cleaned)
    removed = removed or legacy_n > 0
    if text.endswith('\n'):
        cleaned += '\n'
    return cleaned, removed
