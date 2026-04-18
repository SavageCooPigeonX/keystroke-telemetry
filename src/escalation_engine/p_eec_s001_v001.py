"""escalation_engine_seq001_v001_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 35 lines | ~226 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, shutil, subprocess, importlib.util

THRESHOLD_PASSES = 10          # pushes ignored before escalation starts

WARN_COUNTDOWN   = 3           # commits after warning before action

HIGH_CONFIDENCE  = 0.75        # minimum confidence to self-fix

STATE_FILE       = 'logs/escalation_state.json'

LOG_FILE         = 'logs/escalation_log.jsonl'


KNOWN_FIXABLE = {
    'hardcoded_import',        # → auto_apply_import_fixes
    'dead_export',             # → remove unused function
    'over_hard_cap',           # → pigeon split
    'duplicate_docstring',     # → deduplicate
}


LEVEL_NAMES = {
    0: 'REPORT',
    1: 'ASK',
    2: 'INSIST',
    3: 'WARN',
    4: 'ACT',
    5: 'VERIFY',
}


WARN_BLOCK_START = '<!-- pigeon:escalation-warnings -->'

WARN_BLOCK_END   = '<!-- /pigeon:escalation-warnings -->'
