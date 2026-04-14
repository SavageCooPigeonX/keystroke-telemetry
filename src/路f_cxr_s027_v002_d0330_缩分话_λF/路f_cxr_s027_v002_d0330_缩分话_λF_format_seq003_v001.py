"""路f_cxr_s027_v002_d0330_缩分话_λF_format_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 32 lines | ~321 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from src.片w_sm_s026_v002_d0330_缩分话_λF import (
    SHARD_SCHEMA, read_shard_entries, get_shard_summary, list_shards,
    get_unresolved_contradictions,
)
import re

def format_shard_context(routed: list[dict], root: Path | None = None) -> str:
    """Format routed shards into a text block for the enricher prompt.

    If root is provided, also appends unresolved contradictions as warnings.
    """
    if not routed:
        return ''
    lines = ['MEMORY SHARDS (learned patterns from operator history):']
    for r in routed:
        if r['summary']:
            lines.append(f"  [{r['name']}] (relevance={r['relevance']})")
            for sline in r['summary'].splitlines()[1:]:  # skip header
                lines.append(f'  {sline}')

    # append contradiction warnings if any
    if root:
        contras = get_unresolved_contradictions(root)
        if contras:
            lines.append('')
            lines.append(f'⚠ CONTRADICTIONS ({len(contras)} unresolved):')
            for c in contras[:3]:  # top 3 only to save tokens
                lines.append(f"  [{c['shard']}] NEW: {c['new'][:60]} vs OLD: {c['old'][:60]}")

    return '\n'.join(lines)
