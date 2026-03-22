"""registry_seq012_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import json
import re

REGISTRY_FILE = 'pigeon_registry.json'

PIGEON_STEM_RE = re.compile(
    r'^(?P<name>.+)_seq(?P<seq>\d{3})_v(?P<ver>\d{3})'
    r'(?:_d(?P<date>\d{4}))?'
    r'(?:__(?P<slug>[a-z0-9_]+))?$'
)

LC_SEP = '_lc_'  # separator between desc and intent in filename slug
