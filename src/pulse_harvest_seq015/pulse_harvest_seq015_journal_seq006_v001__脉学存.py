"""pulse_harvest_seq015_journal_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _load_latest_journal(root: Path) -> dict | None:
    """Read the most recent entry from prompt_journal.jsonl."""
    journal = root / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return None
    try:
        lines = journal.read_text(encoding='utf-8').strip().splitlines()
        if not lines:
            return None
        return json.loads(lines[-1])
    except (json.JSONDecodeError, OSError):
        return None
