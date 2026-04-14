"""tc_context_profiles_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 27 lines | ~241 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_file_profiles(ctx: dict, repo_root: Path) -> None:
    fprof = repo_root / 'file_profiles.json'
    if not fprof.exists():
        return
    try:
        profiles = json.loads(fprof.read_text('utf-8', errors='ignore'))
        interesting = []
        for name, p in profiles.items():
            fears = p.get('fears', [])
            hes = p.get('avg_hes', 0)
            if fears or hes > 0.5:
                interesting.append({
                    'mod': name,
                    'personality': p.get('personality', '?'),
                    'fears': fears[:3],
                    'hes': round(hes, 2),
                    'v': p.get('version', 0),
                })
        interesting.sort(key=lambda x: x['hes'], reverse=True)
        ctx['file_profiles'] = interesting[:10]
    except Exception:
        pass
