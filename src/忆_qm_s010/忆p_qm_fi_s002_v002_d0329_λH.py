"""query_memory_seq010_fingerprint_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

import re

def _fingerprint(text: str) -> str:
    """Stable semantic fingerprint: strip noise, keep core nouns/verbs."""
    text = text.lower().strip()
    # Remove common filler
    text = re.sub(r'\b(how|do|i|the|a|an|to|in|is|it|can|you|what|why|please|just|me|my|this)\b', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = sorted(set(text.split()))
    return ' '.join(words[:8])  # top 8 content words, sorted = order-invariant
