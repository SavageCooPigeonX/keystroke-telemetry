"""Millisecond-epoch timestamp utility."""


import time

TIMESTAMP_VERSION = "v002"


def _now_ms() -> int:
    return int(time.time() * 1000)
