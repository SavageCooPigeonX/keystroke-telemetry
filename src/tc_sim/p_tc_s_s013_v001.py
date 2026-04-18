"""tc_sim_seq001_v001_memory_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 68 lines | ~654 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json
import re
import sys
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


def update_sim_memory(results: list[SimResult]):
    """Each sim run teaches the system. Per-file accuracy accumulates."""
    mem = _load_sim_memory()
    mem['runs'] = mem.get('runs', 0) + 1
    files = mem.get('files', {})
    for r in results:
        for f in r.context_files:
            if f not in files:
                files[f] = {'times_selected': 0, 'avg_overlap': 0,
                            'best_overlap': 0, 'worst_overlap': 1.0,
                            'total_overlap': 0, 'learnings': []}
            fm = files[f]
            fm['times_selected'] = fm.get('times_selected', 0) + 1
            fm['total_overlap'] = fm.get('total_overlap', 0) + r.word_overlap
            fm['avg_overlap'] = fm['total_overlap'] / fm['times_selected']
            if r.word_overlap > fm.get('best_overlap', 0):
                fm['best_overlap'] = r.word_overlap
            if r.word_overlap < fm.get('worst_overlap', 1.0):
                fm['worst_overlap'] = r.word_overlap
    mem['files'] = files
    _save_sim_memory(mem)
    return mem


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
