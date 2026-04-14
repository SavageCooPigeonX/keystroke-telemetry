"""补p_rwb_s022_v002_d0321_缩分话_λ18_backfill_orchestrator_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 57 lines | ~474 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

def backfill(root: Path) -> int:
    """Run the backfill. Returns count of new entries appended to rework_log.json."""
    score_rework = _load_src('测p_rwd_s009*.py', 'score_rework')
    record_rework = _load_src('测p_rwd_s009*.py', 'record_rework')
    if score_rework is None or record_rework is None:
        return 0

    ai_responses = _load_ai_responses(root)
    if not ai_responses:
        return 0

    keystroke_events = _load_os_keystrokes(root)

    # Load existing rework log for deduplication
    rework_path = root / 'rework_log.json'
    existing: list[dict] = []
    if rework_path.exists():
        try:
            existing = json.loads(rework_path.read_text('utf-8'))
        except Exception:
            existing = []

    seen_keys: set[str] = {
        f"{e.get('ts', '')}|{e.get('query_hint', '')}" for e in existing
    }

    added = 0
    for resp in ai_responses:
        ts_str = resp.get('ts', '')
        if not ts_str:
            continue
        start_ms = _ts_to_ms(ts_str)
        if start_ms == 0:
            continue

        post_events = _events_after(keystroke_events, start_ms)
        score = score_rework(post_events)

        query_hint = str(resp.get('prompt', ''))[:80]
        response_hint = str(resp.get('response', ''))[:200]

        # Dedup by approximate ts bucket (nearest second) + query_hint
        bucket_ts = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).isoformat()
        dedup_key = f"{bucket_ts[:19]}|{query_hint}"
        if dedup_key in seen_keys:
            continue

        seen_keys.add(dedup_key)
        record_rework(root, score, query_text=query_hint, response_text=response_hint)
        added += 1

    return added
