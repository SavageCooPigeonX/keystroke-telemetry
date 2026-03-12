# @pigeon: seq=001 | role=timestamps | depends=[] | exports=[_now_ms] | tokens=~80
"""Millisecond-epoch timestamp utility."""

import time


def _now_ms() -> int:
    return int(time.time() * 1000)
