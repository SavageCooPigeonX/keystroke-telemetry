"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import json
import re

REGISTRY_FILE = 'pigeon_registry.json'

PIGEON_STEM_RE = re.compile(
    r'^(?P<name>.+)_seq(?P<seq>\d{3})_v(?P<ver>\d{3})'
    r'(?:_d(?P<date>\d{4}))?'
    r'(?:__(?P<slug>[a-z0-9_]+))?$'
)

COMPRESSED_STEM_RE = re.compile(
    r'^(?P<glyph>[^\x00-\x7f]*)(?P<state>[pfwu])_(?P<abbrev>[a-z_]+)_s(?P<seq>\d{3,4})_v(?P<ver>\d{3})'
    r'(?:_d(?P<date>\d{4}))?'
    r'(?:_(?P<deps>[^\x00-\x7f]+))?'
    r'(?:_λ(?P<intent>[^_]+))?'
    r'(?:_β(?P<bugs>[a-z]+))?$'
)

LC_SEP = '_lc_'  # separator between desc and intent in filename slug

BUG_KEY_ORDER = ('oc', 'hi', 'hc', 'de', 'dd', 'qn')
