"""tc_sim_seq001_v001_memory_update_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 27 lines | ~291 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import sys
import time

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
