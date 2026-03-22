"""cognitive_reactor_seq014_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import json
import re

FRUSTRATION_STREAK = 3       # consecutive frustrated flushes on same file

HESITATION_THRESHOLD = 0.65  # avg hesitation score to trigger

REACTOR_COOLDOWN_S = 300     # min seconds between reactor fires per file

STATE_FILE = 'logs/cognitive_reactor_state.json'
