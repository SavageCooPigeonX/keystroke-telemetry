"""tc_context_seq001_v001_topology_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 20 lines | ~166 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_codebase_topology(ctx: dict, repo_root: Path) -> None:
    reg = repo_root / 'pigeon_registry.json'
    if not reg.exists():
        return
    try:
        rj = json.loads(reg.read_text('utf-8', errors='ignore'))
        modules = []
        for f in rj.get('files', []):
            modules.append(f"{f.get('name', '?')}({f.get('tokens', 0)}t)")
        ctx['codebase_map'] = {
            'total_modules': rj.get('total', 0),
            'modules': ' '.join(modules[:60]),
        }
    except Exception:
        pass
