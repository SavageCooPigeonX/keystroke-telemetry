"""nametag_seq011_parse_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def parse_nametag(filename: str) -> dict:
    """Parse a nametag filename into components.

    Returns {stem, seq, ver, desc_slug, intent_slug, base_stem}
    """
    m = NAMETAG_PATTERN.match(filename)
    if not m:
        return {'stem': Path(filename).stem, 'seq': '', 'ver': '',
                'desc_slug': '', 'intent_slug': '', 'base_stem': Path(filename).stem}

    base = m.group(1)  # e.g. 'noise_filter_seq007_v001_d0315'
    slug_raw = m.group(2) or ''  # e.g. '__filter_noise_lc_added_drift'
    slug_raw = slug_raw.lstrip('_')

    desc_slug, intent_slug = '', ''
    if slug_raw:
        if LC_SEP in slug_raw:
            desc_slug, intent_slug = slug_raw.split(LC_SEP, 1)
        else:
            desc_slug = slug_raw  # legacy: no intent yet

    seq_m = re.search(r'_seq(\d{3})_v(\d{3})', base)
    seq = seq_m.group(1) if seq_m else ''
    ver = seq_m.group(2) if seq_m else ''

    return {
        'stem': Path(filename).stem,
        'seq': seq,
        'ver': ver,
        'desc_slug': desc_slug,
        'intent_slug': intent_slug,
        'base_stem': base,
    }
