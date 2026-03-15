# @pigeon: seq=001 | role=timestamps | depends=[] | exports=[_now_ms] | tokens=~80
"""Millisecond-epoch timestamp utility."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 8 lines | ~49 tokens
# DESC:   millisecond_epoch_timestamp_utility
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

import time


def _now_ms() -> int:
    return int(time.time() * 1000)
