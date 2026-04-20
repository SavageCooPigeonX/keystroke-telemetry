"""Prompt telemetry daemon — watches composition_recon output for new prompts,
auto-calls log_enriched_entry to keep prompt_telemetry_latest.json fresh.

Fixes chronic staleness: log_enriched_entry only fires when Copilot explicitly
calls it. This daemon detects new composition recon entries and fires it automatically.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

RECON_LOG = ROOT / 'logs' / 'composition_recon_seq001_v001.jsonl'
CHAT_COMPS = ROOT / 'logs' / 'chat_compositions.jsonl'
INTERVAL = 8  # seconds between polls
_last_seen_key: str | None = None
_session_n = 1


def _get_latest_composition() -> dict | None:
    """Read the last entry from composition_recon or chat_compositions."""
    for log in (RECON_LOG, CHAT_COMPS):
        if not log.exists():
            continue
        try:
            lines = log.read_text('utf-8', errors='ignore').strip().splitlines()
            if lines:
                return json.loads(lines[-1])
        except Exception:
            pass
    return None


def _entry_key(entry: dict) -> str:
    return entry.get('ts') or entry.get('session_start') or entry.get('id', '')


def run():
    global _last_seen_key, _session_n
    print('[telemetry-daemon] started', flush=True)

    # Warm start — note current last entry so we only fire on NEW ones
    entry = _get_latest_composition()
    if entry:
        _last_seen_key = _entry_key(entry)

    while True:
        try:
            entry = _get_latest_composition()
            if entry:
                key = _entry_key(entry)
                if key != _last_seen_key:
                    _last_seen_key = key
                    # Extract message text from whatever field is available
                    msg = (entry.get('final_buffer')
                           or entry.get('msg')
                           or entry.get('text')
                           or '')
                    if msg:
                        from src.u_pj_s019_v004_d0420_λRN_βoc import log_enriched_entry  # type: ignore
                        log_enriched_entry(ROOT, msg, [], _session_n)
                        _session_n += 1
                        print(f'[telemetry-daemon] logged session_n={_session_n - 1} msg={msg[:60]!r}', flush=True)
        except Exception as e:
            print(f'[telemetry-daemon] error: {e}', flush=True)
        time.sleep(INTERVAL)


if __name__ == '__main__':
    run()
