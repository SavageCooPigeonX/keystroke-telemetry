"""escalation_engine_seq001_v001_state_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 27 lines | ~240 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _load_state(root: Path) -> dict:
    fp = root / STATE_FILE
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'modules': {}, 'audit_trail': [], 'total_autonomous_fixes': 0}


def _save_state(root: Path, state: dict):
    fp = root / STATE_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')


def _append_log(root: Path, entry: dict):
    fp = root / LOG_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    with open(fp, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
