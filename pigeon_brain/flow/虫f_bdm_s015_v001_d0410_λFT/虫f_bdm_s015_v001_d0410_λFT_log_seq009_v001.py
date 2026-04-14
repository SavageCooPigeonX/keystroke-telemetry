"""虫f_bdm_s015_v001_d0410_λFT_log_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 10 lines | ~106 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _log_chain(root: Path, record: dict) -> None:
    """Append a chain propagation record to the audit log."""
    log = root / BUG_MANIFEST_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
