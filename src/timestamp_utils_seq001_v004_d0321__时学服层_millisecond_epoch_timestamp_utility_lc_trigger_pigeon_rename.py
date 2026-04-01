# @pigeon: seq=001 | role=timestamps | depends=[] | exports=[_now_ms] | tokens=~80
"""Millisecond-epoch timestamp utility."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v004 | 23 lines | ~156 tokens
# DESC:   millisecond_epoch_timestamp_utility
# INTENT: trigger_pigeon_rename
# LAST:   2026-03-21 @ 999b85e
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-21T16:30:00Z
# EDIT_HASH: auto
# EDIT_WHY:  test rename hook trigger
# EDIT_STATE: harvested
# ── /pulse ──

import time

TIMESTAMP_VERSION = "v002"


def _now_ms() -> int:
    return int(time.time() * 1000)
