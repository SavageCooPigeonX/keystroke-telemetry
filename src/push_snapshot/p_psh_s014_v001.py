"""push_snapshot_seq001_v001_history_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 19 lines | ~160 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def get_snapshot_history(root: Path, limit: int = 10) -> list[dict]:
    """Load last N snapshots, most recent first."""
    snap_dir = root / SNAPSHOT_DIR
    if not snap_dir.exists():
        return []
    files = sorted(snap_dir.glob('*.json'), reverse=True)
    # Exclude _latest.json
    files = [f for f in files if f.stem != '_latest']
    result = []
    for f in files[:limit]:
        try:
            result.append(json.loads(f.read_text('utf-8')))
        except Exception:
            continue
    return result
