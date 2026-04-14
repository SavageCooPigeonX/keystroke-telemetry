"""push_snapshot_persistence_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 39 lines | ~355 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

def _save_snapshot(root: Path, commit_hash: str, snapshot: dict):
    snap_dir = root / SNAPSHOT_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)

    # Save by commit hash
    snap_path = snap_dir / f'{commit_hash}.json'
    snap_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), 'utf-8')

    # Update _latest.json
    latest_path = snap_dir / '_latest.json'
    latest_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), 'utf-8')


def _load_previous_snapshot(root: Path, current_commit: str) -> dict | None:
    """Load the snapshot before the current one."""
    snap_dir = root / SNAPSHOT_DIR
    if not snap_dir.exists():
        return None
    files = sorted(snap_dir.glob('*.json'))
    files = [f for f in files if f.stem not in ('_latest', current_commit)]
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text('utf-8'))
    except Exception:
        return None


def _append_drift_log(root: Path, drift_result: dict):
    log_path = root / DRIFT_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    drift_result['ts'] = datetime.now(timezone.utc).isoformat()
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(drift_result) + '\n')
