"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_count_touches_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 34 lines | ~272 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import re

def _count_copilot_touches(root: Path, events: list[dict] | None = None) -> dict[str, float]:
    """Count Copilot file touches from edit_pairs.jsonl with time decay."""
    if events is None:
        events = _load_edit_events(root)
    if not events:
        return {}

    now = datetime.now(timezone.utc)
    scores: dict[str, float] = {}

    try:
        for entry in events:
            mod = entry['module']
            # Time decay
            ts = entry.get('edit_ts', '')
            try:
                edit_time = datetime.fromisoformat(ts)
                age_s = (now - edit_time).total_seconds()
            except Exception:
                age_s = DECAY_HALF_LIFE * 2  # old if unparseable

            weight = math.exp(-0.693 * age_s / DECAY_HALF_LIFE)
            scores[mod] = scores.get(mod, 0.0) + weight
    except Exception:
        pass

    return scores
