"""tc_profile_seq001_v001_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 64 lines | ~742 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from ..tc_constants_seq001_v001 import ROOT
import ast
import json
import re

PROFILE_PATH = ROOT / 'logs' / 'operator_profile_tc.json'

_SECTION_SIGNALS = {
    'debugging': {
        'words': {'fix', 'bug', 'error', 'broken', 'crash', 'fail', 'wrong',
                  'issue', 'trace', 'stack', 'exception', 'undefined', 'null',
                  'why', 'weird', 'wtf', 'wth', 'huh', 'strange'},
        'state_boost': {'frustrated': 0.4, 'hesitant': 0.2},
        'del_ratio_boost': 0.3,  # high deletion = debugging energy
    },
    'infrastructure': {
        'words': {'build', 'pipeline', 'deploy', 'push', 'commit', 'git',
                  'compiler', 'rename', 'manifest', 'registry', 'compliance',
                  'split', 'pigeon', 'config', 'setup', 'wire', 'hook'},
        'state_boost': {'focused': 0.2, 'restructuring': 0.4},
        'del_ratio_boost': 0.0,
    },
    'telemetry': {
        'words': {'telemetry', 'keystroke', 'wpm', 'deletion', 'hesitation',
                  'signal', 'entropy', 'heat', 'profile', 'cognitive', 'state',
                  'composition', 'typing', 'buffer', 'capture', 'stream',
                  'rework', 'drift', 'pulse', 'organism', 'health'},
        'state_boost': {'focused': 0.3},
        'del_ratio_boost': 0.0,
    },
    'exploring': {
        'words': {'what', 'how', 'show', 'explain', 'audit', 'check', 'look',
                  'status', 'health', 'report', 'tell', 'describe', 'where',
                  'architecture', 'design', 'plan', 'think', 'idea', 'maybe'},
        'state_boost': {},
        'del_ratio_boost': -0.1,  # low deletion = browsing not fighting
    },
    'creating': {
        'words': {'create', 'new', 'implement', 'add', 'write', 'generate',
                  'module', 'feature', 'build', 'design', 'prototype', 'draft'},
        'state_boost': {'focused': 0.3, 'restructuring': 0.2},
        'del_ratio_boost': 0.0,
    },
    'reviewing': {
        'words': {'review', 'audit', 'test', 'verify', 'validate', 'compare',
                  'diff', 'change', 'pr', 'merge', 'quality', 'rework'},
        'state_boost': {},
        'del_ratio_boost': 0.0,
    },
}


_INTENT_STOPWORDS = frozenset(
    'the and for with this that from have what when where then than they their '
    'will would could should about been into some also just like more need want '
    'make does dont here were each which still really pretty super actually '
    'kinda right think look looking know going gonna doing done getting much '
    'very even only most many such well back over being said says yeah okay sure '
    'thing things way ways yeah okay want need see try trying you your i me '
    'can cant cannot could should would may might must shall will well '
    'it its a an is are was be to of in on at by up out if or so not no yes '
    'file files module modules code check checking how now got get'.split()
)
