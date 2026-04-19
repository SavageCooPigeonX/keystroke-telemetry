"""tc_sim_seq001_v001_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 21 lines | ~147 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from src.tc_constants_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import json
import re

ROOT = Path(__file__).resolve().parent.parent

SIM_MEMORY_PATH = ROOT / 'logs' / 'sim_memory.json'


_COG_EMOJI = {
    'frustrated': '😤', 'hesitant': '🤔', 'focused': '🎯',
    'abandoned': '💨', 'unknown': '🌀', 'neutral': '😐',
}

_INTENT_VERB = {
    'debugging': 'hunting bugs in', 'building': 'constructing',
    'exploring': 'poking around', 'unknown': 'staring at',
    'fixing': 'patching up',
}
