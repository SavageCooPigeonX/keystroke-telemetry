# @pigeon: seq=001 | role=timestamps | depends=[] | exports=[_now_ms] | tokens=~80
"""Millisecond-epoch timestamp utility."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v003 | 23 lines | ~147 tokens
# DESC:   millisecond_epoch_timestamp_utility
# INTENT: pulse_telemetry_prompt
# LAST:   2026-03-17 @ 9e2a305
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import time

TIMESTAMP_VERSION = "v002"


def _now_ms() -> int:
    return int(time.time() * 1000)
