"""cognitive_reactor_seq014_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 11 lines | ~95 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 1
# ──────────────────────────────────────────────
import json
import re

FRUSTRATION_STREAK = 3       # consecutive frustrated flushes on same file

HESITATION_THRESHOLD = 0.65  # avg hesitation score to trigger

REACTOR_COOLDOWN_S = 300     # min seconds between reactor fires per file

STATE_FILE = 'logs/cognitive_reactor_state.json'
