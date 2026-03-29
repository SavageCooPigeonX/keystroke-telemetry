"""self_fix_seq013_seq_base_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v002 | 18 lines | ~169 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast
import re

def _seq_base(full_name: str) -> str:
    """Extract `logger_seq003` from `logger_seq003_v003_d0317__core_logger`.
    
    Also handles dotted paths: `cognitive.adapter_seq001_v002_...`
    → `cognitive.adapter_seq001`.
    """
    # Split on dots and find the seq part in the last segment
    parts = full_name.rsplit('.', 1)
    last = parts[-1] if len(parts) > 1 else full_name
    prefix = (parts[0] + '.') if len(parts) > 1 else ''
    m = re.match(r'([\w]+_seq\d+)', last)
    if m:
        return prefix + m.group(1)
    return prefix + last.split('_')[0] + '_seq'
