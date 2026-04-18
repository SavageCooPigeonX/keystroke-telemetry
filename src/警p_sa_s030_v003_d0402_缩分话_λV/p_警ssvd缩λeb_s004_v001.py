"""警p_sa_s030_v003_d0402_缩分话_λV_extract_block_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _extract_managed_block(text: str, block_start: str, block_end: str) -> str | None:
    """Return the actual managed block, not an inline example mention."""
    pat = re.compile(
        rf'(?ms)^\s*{re.escape(block_start)}\s*$\n.*?^\s*{re.escape(block_end)}\s*$'
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(0)
