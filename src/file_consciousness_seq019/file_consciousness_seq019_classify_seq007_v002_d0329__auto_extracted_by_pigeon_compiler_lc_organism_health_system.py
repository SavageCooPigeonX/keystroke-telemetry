"""file_consciousness_seq019_classify_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v002 | 28 lines | ~222 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast
import re

def _classify_personality(node, local_fns: set) -> str:
    """Classify function personality type."""
    calls_out = 0
    reads_files = False
    writes_files = False
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            t = _call_target(child)
            if t in local_fns:
                calls_out += 1
            if t in ('open', 'read_text', 'read_bytes', 'glob', 'rglob'):
                reads_files = True
            if t in ('write_text', 'write_bytes', 'write'):
                writes_files = True

    if calls_out >= 3:
        return 'orchestrator'
    if reads_files and writes_files:
        return 'transformer'
    if writes_files:
        return 'writer'
    if reads_files:
        return 'reader'
    return 'worker'
