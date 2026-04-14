"""codebase_transmuter_orchestrator_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 18 lines | ~126 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def transmute_all(root):
    root = Path(root)
    results = {}

    print('  computing global stats...')
    results['stats'] = compute_global_stats(root)

    print('  building numerical mirror...')
    results['numerical'] = build_numerical_mirror(root)

    print('  building narrative mirror...')
    results['narrative'] = build_narrative_mirror(root)

    return results
