"""file_consciousness_seq019_classify_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

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
