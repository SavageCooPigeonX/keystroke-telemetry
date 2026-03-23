"""pulse_harvest_seq015_orchestrator_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def pair_pulse_to_prompt(root: Path, filepath: Path,
                         cognitive_state: str = 'neutral') -> dict | None:
    """Read pulse from file, pair with latest journal entry, write to edit_pairs.
    Returns the paired record or None.
    """
    pulse = read_pulse(filepath)
    if not pulse:
        return None
    journal = _load_latest_journal(root)
    rel = filepath.relative_to(root).as_posix()
    now = datetime.now(timezone.utc)

    # Compute latency: prompt_ts → pulse edit_ts
    latency_ms = 0
    prompt_ts = ''
    prompt_msg = ''
    session_n = 0
    if journal:
        prompt_ts = journal.get('ts', '')
        prompt_msg = journal.get('msg', '')
        session_n = journal.get('session_n', 0)
        try:
            pt = datetime.fromisoformat(prompt_ts)
            et = datetime.fromisoformat(pulse['edit_ts'])
            latency_ms = int((et - pt).total_seconds() * 1000)
        except (ValueError, KeyError):
            pass

    record = {
        'ts': now.isoformat(),
        'prompt_ts': prompt_ts,
        'prompt_msg': prompt_msg[:200],  # truncate for storage
        'file': rel,
        'edit_ts': pulse['edit_ts'],
        'edit_why': pulse['edit_why'],
        'edit_hash': pulse['edit_hash'],
        'latency_ms': latency_ms,
        'state': cognitive_state,
        'session_n': session_n,
    }

    # Append to edit_pairs.jsonl
    pairs_path = root / 'logs' / 'edit_pairs.jsonl'
    pairs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pairs_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

    # Clear the pulse
    clear_pulse(filepath)
    return record


def harvest_all_pulses(root: Path, state: str = 'neutral') -> list[dict]:
    """Walk all .py files under src/, harvest any stamped pulses.
    Called by pigeon post-commit hook as failsafe.
    """
    records = []
    src = root / 'src'
    if not src.is_dir():
        return records
    for py in src.glob('*.py'):
        if py.name.startswith('__'):
            continue
        rec = pair_pulse_to_prompt(root, py, state)
        if rec:
            records.append(rec)
    return records
