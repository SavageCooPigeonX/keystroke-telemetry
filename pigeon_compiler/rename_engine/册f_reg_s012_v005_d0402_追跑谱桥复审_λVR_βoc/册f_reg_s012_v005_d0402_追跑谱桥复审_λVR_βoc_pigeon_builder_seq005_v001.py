"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_pigeon_builder_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
import re

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
