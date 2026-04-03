"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_parse_decomposed_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def parse_pigeon_stem(stem: str) -> dict | None:
    """Parse a Pigeon filename stem into components.

    Old format:
      'noise_filter_seq007_v003_d0315__filter_live_noise_lc_added_drift'
      → {name: 'noise_filter', seq: 7, ver: 3, date: '0315', ...}

    Compressed format:
      '改名f_rr_s006_v005_d0401_追跑拆谱建_λA'
      → {name: '改名f_rr', seq: 6, ver: 5, date: '0401', ..., compressed: True}

    Legacy (no _lc_): treats full slug as desc, intent=''.
    """
    # Try old format first
    m = PIGEON_STEM_RE.match(stem)
    if m:
        slug = m.group('slug') or ''
        desc, intent = '', ''
        if slug:
            if LC_SEP in slug:
                desc, intent = slug.split(LC_SEP, 1)
            else:
                desc = slug
        return {
            'name': m.group('name'),
            'seq': int(m.group('seq')),
            'ver': int(m.group('ver')),
            'date': m.group('date') or '',
            'desc': desc,
            'intent': intent,
            'compressed': False,
        }
    # Try compressed format
    mc = COMPRESSED_STEM_RE.match(stem)
    if mc:
        glyph = mc.group('glyph') or ''
        state = mc.group('state')
        abbrev = mc.group('abbrev')
        bugs = mc.group('bugs') or ''
        return {
            'name': f'{glyph}{state}_{abbrev}',
            'seq': int(mc.group('seq')),
            'ver': int(mc.group('ver')),
            'date': mc.group('date') or '',
            'desc': '',
            'intent': mc.group('intent') or '',
            'compressed': True,
            'glyph': glyph,
            'state': state,
            'abbrev': abbrev,
            'deps': mc.group('deps') or '',
            'bugs': bugs,
            'bug_keys': bug_keys_from_marker(bugs),
        }
    return None
