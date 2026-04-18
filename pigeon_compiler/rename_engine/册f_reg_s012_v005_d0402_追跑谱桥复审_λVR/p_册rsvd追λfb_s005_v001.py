"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_filename_builders_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
import re
from .p_册rsvd追λc_s001_v001 import LC_SEP

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


def build_compressed_filename(glyph: str, state: str, abbrev: str,
                              seq: int, ver: int, date: str = '',
                              deps: str = '', intent: str = '',
                              bugs: str = '') -> str:
    """Construct a compressed Pigeon filename from components.

    build_compressed_filename('改名', 'f', 'rr', 6, 5, '0401', '追跑拆谱建', 'FX', 'ochi')
    → '改名f_rr_s006_v005_d0401_追跑拆谱建_λFX_βochi.py'
    """
    parts = [f'{glyph}{state}_{abbrev}_s{seq:03d}_v{ver:03d}']
    if date:
        parts.append(f'd{date}')
    if deps:
        parts.append(deps)
    if intent:
        parts.append(f'λ{intent}')
    if bugs:
        parts.append(f'β{bugs}')
    return '_'.join(parts) + '.py'
