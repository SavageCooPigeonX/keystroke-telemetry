"""虫f_bdm_s015_v001_d0410_λFT_log_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json

def _log_chain(root: Path, record: dict) -> None:
    """Append a chain propagation record to the audit log."""
    log = root / BUG_MANIFEST_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
