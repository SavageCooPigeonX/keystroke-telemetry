"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import json
import re

COPILOT_PATH = '.github/copilot-instructions.md'

SNAPSHOT_PATH = 'logs/prompt_telemetry_latest.json'

AUDIT_PATH = 'logs/copilot_prompt_audit.json'


PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'

PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'


BLOCK_MARKERS = {
    'task_context': ('<!-- pigeon:task-context -->', '<!-- /pigeon:task-context -->'),
    'task_queue': ('<!-- pigeon:task-queue -->', '<!-- /pigeon:task-queue -->'),
    'operator_state': ('<!-- pigeon:operator-state -->', '<!-- /pigeon:operator-state -->'),
    'prompt_telemetry': (PROMPT_BLOCK_START, PROMPT_BLOCK_END),
    'auto_index': ('<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->'),
    'bug_voices': ('<!-- pigeon:bug-voices -->', '<!-- /pigeon:bug-voices -->'),
}


_INTENT_LABELS = {
    'FX': 'fix',
    'RN': 'rename',
    'RF': 'refactor',
    'SP': 'split',
    'TL': 'telemetry',
    'CP': 'compress',
    'VR': 'verify',
    'FT': 'feature',
    'CL': 'cleanup',
    'OT': 'other',
}


_BUG_LEGEND = {
    'hi': 'hardcoded_import',
    'de': 'dead_export',
    'dd': 'duplicate_docstring',
    'hc': 'high_coupling',
    'oc': 'over_hard_cap',
    'qn': 'query_noise',
}


_BUG_KEY_ORDER = ('oc', 'hi', 'hc', 'de', 'dd', 'qn')


_BUG_PERSONAS = {
    'hi': ('Hardcode Gremlin', 'I weld imports to exact paths and squeal when rename day comes.'),
    'de': ('Dead Export Shade', 'I leave dead functions standing so everyone thinks they still matter.'),
    'dd': ('Mirror Imp', 'I duplicate the same explanation until nobody remembers which copy was first.'),
    'hc': ('Coupling Leech', 'I braid modules together until one cut hurts five files.'),
    'oc': ('Overcap Maw', 'I keep swelling this file past the hard cap. Split me before I eat context.'),
    'qn': ('Noise Imp', 'I fog the query stream until the real intent has to fight to stay visible.'),
}
