"""manifest_builder_seq007_backspace_bursts_seq023_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _find_backspace_bursts(events: list[dict]) -> set[int]:
    """Return indices that are part of a backspace burst (3+ consecutive)."""
    burst_indices = set()
    run_start = None
    for i, ev in enumerate(events):
        if ev.get('event_type') in ('backspace', 'delete'):
            if run_start is None:
                run_start = i
        else:
            if run_start is not None and (i - run_start) >= BACKSPACE_BURST_MIN:
                for j in range(run_start, i):
                    burst_indices.add(j)
            run_start = None
    # Handle burst at end of trail
    if run_start is not None and (len(events) - run_start) >= BACKSPACE_BURST_MIN:
        for j in range(run_start, len(events)):
            burst_indices.add(j)
    return burst_indices
