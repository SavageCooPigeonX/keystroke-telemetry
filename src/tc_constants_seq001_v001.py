"""Shared constants for the thought completer system."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
GEMINI_TIMEOUT = 12
LOG_PATH = ROOT / 'logs' / 'thought_completions.jsonl'
THOUGHT_BUFFER_PATH = ROOT / 'logs' / 'thought_buffer.json'
KEYSTROKE_LOG = ROOT / 'logs' / 'os_keystrokes.jsonl'

DEFAULT_PAUSE_MS = 1200
DEFAULT_CORNER = 'br'
DEFAULT_WIDTH = 560
DEFAULT_HEIGHT = 360
DEFAULT_OPACITY = 0.92
POLL_INTERVAL_MS = 200  # how often we check the keystroke log
