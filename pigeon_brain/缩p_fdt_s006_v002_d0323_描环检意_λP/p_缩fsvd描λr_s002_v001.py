"""缩p_fdt_s006_v002_d0323_描环检意_λP_record_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 21 lines | ~187 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

def record_death(root: Path, classification: dict, job_id: str) -> None:
    """Append a death event to execution_death_log.json."""
    log_path = root / DEATH_STORE
    try:
        existing = json.loads(log_path.read_text("utf-8")) if log_path.exists() else []
    except Exception:
        existing = []

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        **classification,
    }
    existing.append(entry)
    log_path.write_text(json.dumps(existing[-MAX_ENTRIES:], indent=2),
                        encoding="utf-8")
