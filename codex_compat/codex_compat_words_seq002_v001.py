"""codex_compat_words_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _words(text: str) -> list[str]:
    return [part.strip(".,;:!?()[]{}\"'`") for part in str(text).split() if part.strip(".,;:!?()[]{}\"'`")]
