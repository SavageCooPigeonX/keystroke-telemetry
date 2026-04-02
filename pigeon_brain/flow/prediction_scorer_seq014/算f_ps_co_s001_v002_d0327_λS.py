"""prediction_scorer_seq014_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 11 lines | ~73 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
import json
import re

SCORED_CACHE_FILE = "prediction_scores.json"

CALIBRATION_FILE = "prediction_calibration.json"

MAX_SCORED = 200

EVAL_WINDOW = 5  # score against next N prompts after prediction
