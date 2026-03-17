# @pigeon: seq=001 | role=timestamps | depends=[] | exports=[_now_ms] | tokens=~80
"""Millisecond-epoch timestamp utility."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 16 lines | ~112 tokens
# DESC:   millisecond_epoch_timestamp_utility
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
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
