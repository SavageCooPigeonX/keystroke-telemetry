"""codebase_transmuter_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 42 lines | ~427 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import time

SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
             '.egg-info', 'pigeon_code.egg-info', 'build', 'stress_logs',
             'test_logs', 'demo_logs', 'logs'}


PY_DIRS = ['src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer', 'client']


APPROX_CHARS_PER_TOKEN = 4.0


MOOD_INTROS = {
    'unhinged': "i've been touched {T} times by copilot and i am NOT okay. "
                "entropy is leaking from every function.",
    'paranoid': "copilot keeps coming back to me ({T} edits). "
                "what does it want. what does it know.",
    'anxious': "{T} copilot touches. each one left a mark. "
               "i can feel the uncertainty in my imports.",
    'cautious': "mildly concerned. {T} copilot visits so far. "
                "monitoring the situation.",
    'chill': "vibing. low entropy. copilot barely knows i exist.",
}


DEMON_TEMPLATES = {
    'oc': "THE OVERCAP MAW — i keep swelling. {lines} lines and growing. "
          "the compiler wants to split me but i refuse to die.",
    'hi': "THE HARDCODED IMPORT DEMON — someone wrote a literal path "
          "in my imports. it burns.",
    'de': "THE DEAD EXPORT PHANTOM — i export things nobody imports. "
          "screaming into the void.",
    'dd': "THE DUPLICATE DOCSTRING — my documentation is having an "
          "identity crisis. two of everything.",
    'hc': "THE COUPLING PARASITE — i'm fused to too many other files. "
          "if one falls, i fall.",
    'qn': "THE QUERY NOISE GREMLIN — my queries are polluted with "
          "junk. signal-to-noise is trash.",
}
