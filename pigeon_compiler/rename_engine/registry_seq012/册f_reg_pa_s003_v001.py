"""registry_seq012_parser_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def parse_pigeon_stem(stem: str) -> dict | None:
    """Parse a Pigeon filename stem into components.

    'noise_filter_seq007_v003_d0315__filter_live_noise_lc_added_drift'
    → {name: 'noise_filter', seq: 7, ver: 3, date: '0315',
       desc: 'filter_live_noise', intent: 'added_drift'}

    Legacy (no _lc_): treats full slug as desc, intent=''.
    """
    m = PIGEON_STEM_RE.match(stem)
    if not m:
        return None
    slug = m.group('slug') or ''
    desc, intent = '', ''
    if slug:
        if LC_SEP in slug:
            desc, intent = slug.split(LC_SEP, 1)
        else:
            desc = slug  # legacy: whole slug is desc
    return {
        'name': m.group('name'),
        'seq': int(m.group('seq')),
        'ver': int(m.group('ver')),
        'date': m.group('date') or '',
        'desc': desc,
        'intent': intent,
    }


def build_pigeon_filename(name: str, seq: int, ver: int,
                          date: str = '', desc: str = '',
                          intent: str = '') -> str:
    """Construct a full Pigeon filename from components.

    build_pigeon_filename('noise_filter', 7, 3, '0315',
                          'filter_live_noise', 'added_drift')
    → 'noise_filter_seq007_v003_d0315__filter_live_noise_lc_added_drift.py'
    """
    parts = f'{name}_seq{seq:03d}_v{ver:03d}'
    if date:
        parts += f'_d{date}'
    if desc and intent:
        parts += f'__{desc}{LC_SEP}{intent}'
    elif desc:
        parts += f'__{desc}'
    return parts + '.py'
