"""nametag_seq011_slugify_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re
from .牌f_nam_co_s001_v001 import MAX_DESC_WORDS

def slugify(text: str, max_words: int = MAX_DESC_WORDS) -> str:
    """Convert a sentence to a filename-safe slug.

    'Filter background noise from live streams' → 'filter_background_noise'
    'Resend API Client' → 'resend_api_client'
    """
    # Strip filename prefixes like "module.py — "
    if ' — ' in text:
        text = text.split(' — ', 1)[1]
    elif ' - ' in text:
        parts = text.split(' - ', 1)
        if len(parts[0].split()) <= 3:
            text = parts[1]

    # Remove trailing period
    text = text.rstrip('.')

    # Convert to lowercase, replace non-alpha with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

    # Strip leaked seq/ver patterns like "seq007_v001"
    slug = re.sub(r'_?seq\d{3}_v\d{3}_?', '_', slug).strip('_')

    # Trim to max words
    words = slug.split('_')
    words = [w for w in words if w]  # remove empties
    if len(words) > max_words:
        words = words[:max_words]

    slug = '_'.join(words)

    # Hard limit on total chars
    if len(slug) > MAX_SLUG_CHARS:
        slug = slug[:MAX_SLUG_CHARS].rstrip('_')

    return slug
