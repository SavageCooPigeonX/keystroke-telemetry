"""push_snapshot_registry_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 22 lines | ~232 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_registry(root: Path) -> dict:
    p = root / 'pigeon_registry.json'
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text('utf-8'))
        # Registry format: {'generated': ..., 'total': N, 'files': [list of dicts]}
        files = data.get('files', data) if isinstance(data, dict) else data
        if isinstance(files, list):
            # Exclude build/ artifacts — they're compressed copies, not source
            return {m.get('name', f'mod_{i}'): m for i, m in enumerate(files)
                    if isinstance(m, dict)
                    and not m.get('path', '').startswith('build/')}
        if isinstance(files, dict):
            return {k: v for k, v in files.items() if isinstance(v, dict)}
        return {}
    except Exception:
        return {}
