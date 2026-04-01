""".operator_stats_seq008_v008_d0331__persi_artifact_detection_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _is_artifact_record(record: dict) -> bool:
    """Detect synthetic micro-batches / background flushes that should not shape the baseline."""
    wpm = record.get("wpm", 0)
    # Any record with superhuman WPM is a background flush event regardless of submit flag
    if wpm > WPM_HUMAN_MAX:
        return True
    keys = record.get("keys", 0)
    hes = record.get("hesitation", 0)
    del_ratio = record.get("del_ratio", 0)
    submitted = record.get("submitted", True)
    return (
        not submitted
        and keys <= 3
        and wpm >= 180
        and hes >= 0.95
        and del_ratio >= 0.3
    )
