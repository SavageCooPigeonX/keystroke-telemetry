"""escalation_engine_rollback_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 48 lines | ~411 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _create_rollback_point(root: Path, registry_entry: dict) -> dict | None:
    """Create a backup copy before autonomous modification."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return None
    backup_dir = root / 'logs' / 'escalation_backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_name = f"{fpath.stem}_{ts}.py.bak"
    backup_path = backup_dir / backup_name
    shutil.copy2(fpath, backup_path)
    return {
        'original': str(fpath),
        'backup': str(backup_path),
        'ts': ts,
        'ver': registry_entry.get('ver', 0),
    }


def _rollback(root: Path, rollback_point: dict) -> bool:
    """Restore a file from its backup."""
    try:
        backup = Path(rollback_point['backup'])
        original = Path(rollback_point['original'])
        if backup.exists():
            shutil.copy2(backup, original)
            return True
    except Exception:
        pass
    return False


def _verify_fix(root: Path, module: str) -> bool:
    """Run basic compliance check after a fix."""
    try:
        result = subprocess.run(
            ['py', 'test_all.py'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=str(root), timeout=120,
        )
        return 'ALL TESTS PASSED' in result.stdout or result.returncode == 0
    except Exception:
        return False
