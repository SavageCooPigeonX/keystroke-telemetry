"""nametag_seq011_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import re

MAX_DESC_WORDS = 5

MAX_INTENT_WORDS = 3

MAX_SLUG_CHARS = 50

DESC_SEPARATOR = '__'

LC_SEP = '_lc_'  # separator between desc and intent


NAMETAG_PATTERN = re.compile(
    r'^(.+_seq\d{3}_v\d{3}(?:_d\d{4})?)(__[a-z0-9_]+)?\.py$'
)
