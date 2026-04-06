"""prediction_scorer_seq014_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

import json
import re

SCORED_CACHE_FILE = "prediction_scores.json"

CALIBRATION_FILE = "prediction_calibration.json"

MAX_SCORED = 200

EVAL_WINDOW = 5  # score against next N prompts after prediction
