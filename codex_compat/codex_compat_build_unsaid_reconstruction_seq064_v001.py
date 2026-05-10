"""codex_compat_build_unsaid_reconstruction_seq064_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _build_unsaid_reconstruction(final_text: str, deleted_words: list[str]) -> str:
    if not deleted_words:
        return ""
    return f"{final_text[:120]}... (also considered: {' '.join(deleted_words[:8])})"
