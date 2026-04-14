"""tc_sim_memory_core_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 43 lines | ~389 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json
import re
import time

def _load_sim_memory() -> dict:
    if SIM_MEMORY_PATH.exists():
        try:
            return json.loads(SIM_MEMORY_PATH.read_text('utf-8', errors='ignore'))
        except Exception:
            pass
    return {'files': {}, 'bugs_found': [], 'bugs_fixed': [], 'runs': 0}


def _save_sim_memory(mem: dict):
    SIM_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    mem['updated'] = datetime.now(timezone.utc).isoformat()
    SIM_MEMORY_PATH.write_text(json.dumps(mem, ensure_ascii=False, indent=1),
                                encoding='utf-8')


def record_bug_found(mem: dict, bug_id: str, description: str, file: str):
    """Record a bug discovered by sim analysis."""
    mem.setdefault('bugs_found', []).append({
        'id': bug_id, 'desc': description, 'file': file,
        'ts': datetime.now(timezone.utc).isoformat(), 'fixed': False,
    })
    _save_sim_memory(mem)


def record_bug_fixed(mem: dict, bug_id: str, fix_description: str):
    """Record that a sim-discovered bug was fixed."""
    for b in mem.get('bugs_found', []):
        if b['id'] == bug_id:
            b['fixed'] = True
            b['fix'] = fix_description
            b['fixed_ts'] = datetime.now(timezone.utc).isoformat()
    mem.setdefault('bugs_fixed', []).append({
        'id': bug_id, 'fix': fix_description,
        'ts': datetime.now(timezone.utc).isoformat(),
    })
    _save_sim_memory(mem)
