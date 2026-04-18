"""scale_inference_seq001_v001_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 37 lines | ~260 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

SCALES = {
    1: 'SENTENCE',
    2: 'PARAGRAPH',
    3: 'FULL_WRITE',
    4: 'PAPER',
}


_ACTION_WORDS = {
    'fix': 3, 'add': 3, 'wire': 3, 'patch': 3, 'implement': 3, 'build': 3,
    'create': 3, 'write': 3, 'remove': 3, 'delete': 3, 'replace': 3,
    'refactor': 3, 'move': 3, 'rename': 3, 'split': 3, 'merge': 3,
    'connect': 3, 'hook': 3, 'plug': 3, 'inject': 3, 'update': 3,
}


_QUESTION_WORDS = {
    'why': 2, 'how': 2, 'what': 2, 'explain': 2, 'show': 2,
    'describe': 2, 'compare': 2, 'analyze': 2, 'audit': 2,
    'check': 2, 'review': 2, 'investigate': 2, 'debug': 2,
}


_ARCHITECTURE_WORDS = {
    'redesign': 4, 'rethink': 4, 'rearchitect': 4, 'plan': 4,
    'strategy': 4, 'roadmap': 4, 'document': 4, 'paper': 4,
    'proposal': 4, 'migration': 4, 'overhaul': 4,
}


_MODULE_PATTERN = re.compile(r'^the\s+[a-zA-Z_][a-zA-Z0-9_]*\s*$', re.IGNORECASE)


_WHAT_IF_PATTERN = re.compile(r'what\s+if\s+we\s+\w+', re.IGNORECASE)
