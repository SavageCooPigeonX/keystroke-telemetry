"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 27 lines | ~143 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import re

HEAT_STORE      = 'file_heat_map.json'

COPILOT_BRAIN_STORE = 'logs/copilot_brain_map.json'

DECAY_HALF_LIFE = 86400 * 3  # 3 days — touches decay to half relevance

HIGH_VER_THRESH = 5

QUICK_RETOUCH_S = 20 * 60

HIGH_LATENCY_MS = 5 * 60_000


STATE_ENTROPY = {
    'focused': 0.05,
    'neutral': 0.08,
    'restructuring': 0.18,
    'abandoned': 0.24,
    'hesitant': 0.28,
    'frustrated': 0.32,
    'confused': 0.30,
    'unknown': 0.12,
}
