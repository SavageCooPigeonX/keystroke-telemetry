"""manifest_builder_seq007_seq_extract_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _extract_seq(filename: str) -> str:
    """Extract seq number from pigeon filename."""
    m = re.search(r'_seq(\d+)', filename)
    return m.group(1) if m else ''
