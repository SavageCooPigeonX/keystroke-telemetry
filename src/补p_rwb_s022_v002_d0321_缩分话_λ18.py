"""Rework backfill — reconstructs historical rework scores from chat history.

Reads past AI responses from ai_responses.jsonl (synced from vscdb),
pairs each response timestamp with the 30s of keystroke events that
followed it in os_keystrokes.jsonl, scores them with score_rework(),
and appends any new entries to rework_log.json.

Deduplicates by response ts + query_hint — safe to run repeatedly.
"""
from __future__ import annotations
import glob as _glob
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


REWORK_WINDOW_MS = 30_000   # 30s post-response window


def _load_src(pattern: str, *symbols):
    matches = sorted(_glob.glob(f'src/{pattern}'))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location('_dyn', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if len(symbols) == 1:
        return getattr(mod, symbols[0], None)
    return tuple(getattr(mod, s, None) for s in symbols)


def _load_ai_responses(root: Path) -> list[dict]:
    """Load ai_responses.jsonl — each line is a JSON record with ts, prompt, response."""
    p = root / 'logs' / 'ai_responses.jsonl'
    if not p.exists():
        return []
    entries = []
    for line in p.read_text('utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def _load_os_keystrokes(root: Path) -> list[dict]:
    """Load os_keystrokes.jsonl sorted by ts (ms epoch)."""
    p = root / 'logs' / 'os_keystrokes.jsonl'
    if not p.exists():
        return []
    events = []
    for line in p.read_text('utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    events.sort(key=lambda e: e.get('ts', 0))
    return events


def _ts_to_ms(ts_str: str) -> float:
    """Parse ISO-8601 ts to epoch ms. Returns 0.0 on failure."""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.timestamp() * 1000
    except Exception:
        return 0.0


def _events_after(keystroke_events: list[dict], start_ms: float) -> list[dict]:
    """Return keystroke events in [start_ms, start_ms + REWORK_WINDOW_MS]."""
    end_ms = start_ms + REWORK_WINDOW_MS
    return [e for e in keystroke_events if start_ms <= e.get('ts', 0) <= end_ms]


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


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    n = backfill(root)
    print(json.dumps({"backfilled": n}))
