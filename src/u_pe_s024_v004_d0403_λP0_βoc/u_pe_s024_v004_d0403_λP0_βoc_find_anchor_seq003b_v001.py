"""u_pe_s024_v004_d0403_λP0_βoc_find_anchor_seq003b_v001.py — Auto-extracted by Pigeon Compiler."""
import re

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
