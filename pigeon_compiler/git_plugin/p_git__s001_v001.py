"""git_plugin_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

TOKEN_RATIO = 4  # chars per token


BOX_RE = re.compile(
    r'^# ── pigeon ─[^\n]*\n(?:# [^\n]*\n)*# ─{10,}─*\n',
    re.MULTILINE,
)

_AUTO_INDEX_RE = re.compile(
    r'<!-- pigeon:auto-index -->.*?<!-- /pigeon:auto-index -->',
    re.DOTALL,
)

_ROOT_DEBUG = re.compile(r'^_')


_BUG_KEY_MAP = {
    'hardcoded_import': 'hi',
    'dead_export': 'de',
    'duplicate_docstring': 'dd',
    'high_coupling': 'hc',
    'over_hard_cap': 'oc',
    'query_noise': 'qn',
}


_BUG_KEY_ORDER = ('oc', 'hi', 'hc', 'de', 'dd', 'qn')


_BUG_ENTITY_POOL = {
    'hi': ('Needle Imp', 'Path Wraith', 'Anchor Gremlin'),
    'de': ('Export Shade', 'Dead Echo', 'Null Moth'),
    'dd': ('Mirror Imp', 'Echo Quill', 'Twin Static'),
    'hc': ('Coupling Leech', 'Knot Familiar', 'Tangle Fiend'),
    'oc': ('Overcap Maw', 'Shard Hunger', 'Split Fiend'),
    'qn': ('Noise Imp', 'Query Moth', 'Static Gremlin'),
}


_OPERATOR_STATE_RE = re.compile(
    r'<!-- pigeon:operator-state -->.*?<!-- /pigeon:operator-state -->',
    re.DOTALL,
)
