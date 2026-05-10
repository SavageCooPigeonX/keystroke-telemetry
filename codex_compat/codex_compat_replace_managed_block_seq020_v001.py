"""codex_compat_replace_managed_block_seq020_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _replace_managed_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _match: block, text)
    return text.rstrip() + "\n\n" + block + "\n"
