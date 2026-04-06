"""learning_loop_seq013_journal_loader_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
from typing import Any
import json

def _load_journal_entries(root: Path, after_line: int = 0) -> list[dict[str, Any]]:
    """Load prompt journal entries after a given line number."""
    journal = root / "logs" / "prompt_journal.jsonl"
    if not journal.exists():
        return []
    lines = journal.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for i, line in enumerate(lines):
        if i < after_line:
            continue
        try:
            entry = json.loads(line)
            entry["_line_num"] = i
            entries.append(entry)
        except json.JSONDecodeError:
            continue
    return entries
