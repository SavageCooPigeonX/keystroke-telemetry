"""nametag_seq011_build_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def build_nametag(stem: str, desc_slug: str, intent_slug: str = '') -> str:
    """Combine a Pigeon stem with desc + intent.

    'noise_filter_seq007_v001' + 'filter_live_noise' + 'added_drift'
    → 'noise_filter_seq007_v001__filter_live_noise_lc_added_drift.py'

    Without intent:
    'noise_filter_seq007_v001' + 'filter_live_noise'
    → 'noise_filter_seq007_v001__filter_live_noise.py'
    """
    if not desc_slug:
        return f'{stem}.py'
    if intent_slug:
        return f'{stem}{DESC_SEPARATOR}{desc_slug}{LC_SEP}{intent_slug}.py'
    return f'{stem}{DESC_SEPARATOR}{desc_slug}.py'
