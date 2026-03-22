"""heal_seq009_log_writer_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _write_heal_log(root: Path, report: dict) -> None:
    """Append to heal log (keeps last 50 entries)."""
    log_path = root / HEAL_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if log_path.exists():
        try:
            history = json.loads(log_path.read_text(encoding='utf-8'))
        except Exception:
            history = []

    history.append(report)
    # Keep last 50
    history = history[-50:]

    log_path.write_text(
        json.dumps(history, indent=2, default=str),
        encoding='utf-8',
    )

HEAL_LOG = 'pigeon_compiler/rename_engine/heal_log.json'
