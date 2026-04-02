"""u_pe_s024_v002_d0402_λC_block_utils_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
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


def _find_insert_anchor(text: str) -> int:
    """Insert before the first real managed block line, not inline examples."""
    markers = (
        '<!-- pigeon:task-context -->',
        '<!-- pigeon:task-queue -->',
        '<!-- pigeon:operator-state -->',
        '<!-- pigeon:prompt-telemetry -->',
        '<!-- pigeon:auto-index -->',
    )
    hits = []
    for marker in markers:
        m = re.search(rf'(?m)^\s*{re.escape(marker)}\s*$', text)
        if m:
            hits.append(m.start())
    return min(hits) if hits else -1
