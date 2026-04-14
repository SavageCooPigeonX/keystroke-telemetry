"""codebase_detector_count_modules_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 17 lines | ~154 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _count_modules(root: Path, kind: str) -> int:
    if kind == 'pigeon':
        reg = root / 'pigeon_registry.json'
        if reg.exists():
            try:
                data = json.loads(reg.read_text('utf-8', errors='ignore'))
                return len(data.get('files', []))
            except Exception:
                pass
    count = 0
    for pat in ('src/**/*.py', 'lib/**/*.py', 'src/**/*.ts', 'src/**/*.rs'):
        count += len(list(root.glob(pat)))
    return count
